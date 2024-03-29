from sc2.bot_ai import BotAI, Race
from sc2.data import Result
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId


class CompetitiveBot(BotAI):
    NAME: str = "BurningBot"

    RACE: Race = Race.Terran
    """
        Race.Terran
        Race.Zerg
        Race.Protoss
        Race.Random
    """
    isAttacking = False
    isPreparingAttack = False
    barracksCount: int = 0
    depotWallCount: int = 0
    depotWallPos: list = []
    async def on_start(self):
        """
        This code runs once at the start of the game
        Do things here before the game starts
        """
        print("Game started")

    async def on_step(self, iteration: int):
        await self.distribute_workers()
        await self.build_workers(UnitTypeId.SCV)
        await self.build_barracks()
        await self.build_ramp_depots()
        pass

    async def on_end(self, result: Result):
        """
        This code runs once at the end of the game
        Do things here after the game ends
        """
        print("Game ended.")

    async def get_workers_count(self):
        worker_count: int = self.workers().count()
        return worker_count

    async def build_workers(self, workerType):
        nexus = self.townhalls.ready.random
        if (
            self.can_afford(workerType)
            and nexus.is_idle
            and self.workers.amount < self.townhalls.amount * 22
        ):
            nexus.train(workerType)

    async def build_supply_structure(self, supply_structure_type):
        cc = self.townhalls.ready.random
        position = cc.position.towards(self.enemy_start_locations[0], 10)
        if self.depotWallCount >= 2:
            if (
                self.supply_left < 3
                and self.supply_cap <= 190
                and self.already_pending(supply_structure_type) == 0
                and self.can_afford(supply_structure_type)
            ):
                await self.build(supply_structure_type, near=position)


    async def build_ramp_depots(self):
        self.depotWallPos = list(self.main_base_ramp.corner_depots)
        if (
                self.supply_left < 3
                and self.can_afford(UnitTypeId.SUPPLYDEPOT)
                and self.depotWallCount < 2
                and self.already_pending(UnitTypeId.SUPPLYDEPOT) == 0
        ):
            if self.depotWallCount == 0:
                await self.build(UnitTypeId.SUPPLYDEPOT, near=self.depotWallPos[0])
                self.depotWallCount += 1
                await self.chat_send("building first depot")
            elif self.depotWallCount == 1:
                await self.build(UnitTypeId.SUPPLYDEPOT, near=self.depotWallPos[1])
                self.depotWallCount += 1
                await self.chat_send("building second depot")
                await self.chat_send(str(self.depotWallCount))
        else:
            await self.build_supply_structure(UnitTypeId.SUPPLYDEPOT)

    async def lower_ramp_depot(self):
        #get depot closes to main base ramp and lower so marines can pass
            depot = self.structures(UnitTypeId.SUPPLYDEPOT).closest_to(self, near=self.main_base_ramp.barracks_correct_placement)
            if (
                    self.structures(depot).ready
            ):
               depot(AbilityId.MORPH_SUPPLYDEPOT_LOWER)


    async def build_barracks(self):
        if self.barracksCount == 0:
            if (
                self.structures(UnitTypeId.SUPPLYDEPOT).ready
                and self.can_afford(UnitTypeId.BARRACKS)
            ):
                barracksPos = self.main_base_ramp.barracks_correct_placement
                await self.build(UnitTypeId.BARRACKS, near=barracksPos)
                self.barracksCount += 1
                await self.chat_send(str(barracksPos))
                await self.chat_send(str(self.barracksCount))


    async def build_gas(self):
        if self.structures(UnitTypeId.GATEWAY):
            for nexus in self.townhalls.ready:
                vgs = self.vespene_geyser.closer_than(15, nexus)
                for vg in vgs:
                    if not self.can_afford(UnitTypeId.ASSIMILATOR):
                        break
                    worker = self.select_build_worker(vg.position)
                    if worker is None:
                        break
                    if not self.gas_buildings or not self.gas_buildings.closer_than(1, vg):
                        worker.build(UnitTypeId.ASSIMILATOR, vg)
                        worker.stop(queue=True)

    async def build_cybercore(self):
        if self.structures(UnitTypeId.PYLON).ready:
            pylon = self.structures(UnitTypeId.PYLON).ready.random
            if self.structures(UnitTypeId.GATEWAY).ready:
                if not self.structures(UnitTypeId.CYBERNETICSCORE):
                    if (
                        self.can_afford(UnitTypeId.CYBERNETICSCORE)
                        and self.already_pending(UnitTypeId.CYBERNETICSCORE) == 0
                    ):
                        await self.build(UnitTypeId.CYBERNETICSCORE, near=pylon)

    async def train_stalkers(self):
        for gateway in self.structures(UnitTypeId.GATEWAY).ready:
            if (
                self.can_afford(UnitTypeId.STALKER)
                and gateway.is_idle
            ):
                gateway.train(UnitTypeId.STALKER)

    async def build_four_gates(self):
        if self.barracksCount < 4:
            if (
                self.structures(UnitTypeId.PYLON).ready
                and self.structures(UnitTypeId.CYBERNETICSCORE).exists
                and self.can_afford(UnitTypeId.GATEWAY)
            ):
                pylon = self.structures(UnitTypeId.PYLON).ready.random
                await self.build(UnitTypeId.GATEWAY, near=pylon)
                self.barracksCount += 1
                await self.chat_send(str(self.barracksCount))

    async def research_warpgate(self):
        if (
            self.structures(UnitTypeId.CYBERNETICSCORE).ready
            and self.can_afford(UpgradeId.WARPGATERESEARCH)
        ):
            self.research(UpgradeId.WARPGATERESEARCH)

    async def use_chrono_boost(self):
        if self.structures(UnitTypeId.PYLON):
            nexus = self.townhalls.ready.random
            if (
                not self.structures(UnitTypeId.CYBERNETICSCORE).ready
                and self.structures(UnitTypeId.PYLON).amount > 0
            ):
                if nexus.energy >= 50:
                    nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, nexus)
            else:
                if nexus.energy >= 50 and self.units(UnitTypeId.PROBE).amount > 18:
                    nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST,
                          self.structures(UnitTypeId.CYBERNETICSCORE).ready.random)

    async def attack(self):
        if self.units(UnitTypeId.STALKER).ready.amount > 0:
            stalkers = self.units(UnitTypeId.STALKER).ready.idle

            for stalker in stalkers:
                if self.units(UnitTypeId.STALKER).amount > 10:
                    stalker.attack(self.enemy_start_locations[0])
                    if not self.isAttacking:
                        self.isAttacking = True

    async def warp_stalkers_to_proxy(self):
        for warpgate in self.structures(UnitTypeId.WARPGATE).ready:
            abilities = await self.get_available_abilities(warpgate)
            if self.isAttacking:
                proxyPylon = self.structures(UnitTypeId.PYLON).closest_to(self.enemy_start_locations[0])
            else:
                proxyPylon = self.structures(UnitTypeId.PYLON).ready.random
            if AbilityId.WARPGATETRAIN_STALKER in abilities and self.can_afford(UnitTypeId.STALKER):
                warpgate.warp_in(UnitTypeId.STALKER, proxyPylon.position.random_on_distance(3))

    async def build_proxy_pylon(self):
        if (
            self.proxyPylonCounter < 1
            and self.isAttacking
            and self.can_afford(UnitTypeId.PYLON)
        ):
            await self.build(UnitTypeId.PYLON, near=self.game_info.map_center.towards(self.enemy_start_locations[0], 20))
            self.proxyPylonCounter = 1