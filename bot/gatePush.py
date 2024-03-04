from sc2.bot_ai import BotAI
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId


class gatePush(BotAI):

    proxyPylonCounter: int = 0
    isAttacking = False
    isPreparingAttack = False
    gatewayCount: int = 0

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
        nexus = self.townhalls.ready.random
        position = nexus.position.towards(self.enemy_start_locations[0], 10)

        if (
            self.supply_left < 3
            and self.supply_cap <= 190
            and self.already_pending(supply_structure_type) == 0
            and self.can_afford(supply_structure_type)
        ):
            await self.build(supply_structure_type, near=position)

    async def build_barracks(self):
        if self.gatewayCount == 0:
            if (
                self.structures(UnitTypeId.PYLON).ready
                and self.can_afford(UnitTypeId.GATEWAY)
            ):
                pylon = self.structures(UnitTypeId.PYLON).ready.random
                await self.build(UnitTypeId.GATEWAY, near=pylon)
                self.gatewayCount += 1
                await self.chat_send(str(self.gatewayCount))


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
        if self.gatewayCount < 4:
            if (
                self.structures(UnitTypeId.PYLON).ready
                and self.structures(UnitTypeId.CYBERNETICSCORE).exists
                and self.can_afford(UnitTypeId.GATEWAY)
            ):
                pylon = self.structures(UnitTypeId.PYLON).ready.random
                await self.build(UnitTypeId.GATEWAY, near=pylon)
                self.gatewayCount += 1
                await self.chat_send(str(self.gatewayCount))

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

    async def executeBO(self):
        await self.distribute_workers()
        await self.build_workers(UnitTypeId.PROBE)
        await self.build_supply_structure(UnitTypeId.PYLON)
        await self.use_chrono_boost()
        await self.build_barracks()
        await self.build_gas()
        await self.build_cybercore()
        await self.train_stalkers()
        await self.build_four_gates()
        await self.research_warpgate()
        await self.attack()
        await self.warp_stalkers_to_proxy()
        await self.build_proxy_pylon()
        pass