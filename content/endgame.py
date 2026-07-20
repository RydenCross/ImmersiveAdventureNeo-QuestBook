from generator.builder import ChapterBuilder
from model import Project


def build_endgame(
    project: Project,
    create_complete: str,
    actually_additions_complete: str,
    ars_complete: str,
    apotheosis_complete: str,
    ae2_complete: str,
    mekanism_complete: str,
) -> str:
    chapter = ChapterBuilder(
        project,
        slug="10_endgame",
        title="Endgame",
        icon="minecraft:nether_star",
        description=(
            "Unify every major progression path into reliable infrastructure, "
            "large-scale automation, and final mastery challenges."
        ),
    )

    convergence = (
        chapter.quest(
            "convergence",
            "The Great Convergence",
            "minecraft:nether_star",
            (
                "You have mastered the pack's major disciplines. Bring Create, Actually Additions, "
                "Ars Nouveau, Apotheosis, Applied Energistics 2, and Mekanism together into one base."
            ),
            0,
            0,
        )
        .depends_on(
            create_complete,
            actually_additions_complete,
            ars_complete,
            apotheosis_complete,
            ae2_complete,
            mekanism_complete,
        )
        .checkmark()
        .finish()
    )

    command_center = (
        chapter.quest(
            "command_center",
            "Build a Command Center",
            "ae2:crafting_terminal",
            (
                "Create a central operations room that exposes storage, crafting, power status, "
                "factory controls, and emergency shutdowns without forcing you to visit every machine."
            ),
            2,
            -4,
        )
        .depends_on(convergence)
        .checkmark()
        .finish()
    )

    power_backbone = (
        chapter.quest(
            "power_backbone",
            "One Power Backbone",
            "mekanism:ultimate_universal_cable",
            (
                "Connect your major workshops to a protected high-capacity power backbone with "
                "buffered storage and clearly separated generation, distribution, and machine loads."
            ),
            4,
            -4,
        )
        .depends_on(command_center)
        .checkmark()
        .finish()
    )

    monitored_grid = (
        chapter.quest(
            "monitored_grid",
            "A Grid You Can Read",
            "create:display_board",
            (
                "Display meaningful system information such as stored energy, reactor state, "
                "critical stock levels, or factory activity where operators can see it immediately."
            ),
            6,
            -4,
        )
        .depends_on(power_backbone)
        .checkmark()
        .finish()
    )

    resilient_base = (
        chapter.quest(
            "resilient_base",
            "Design for Failure",
            "minecraft:redstone_torch",
            (
                "Add alarms, shutdown controls, overflow handling, and reserve storage so a single "
                "empty tank, full output, or broken supply route cannot disable the entire base."
            ),
            8,
            -4,
        )
        .depends_on(monitored_grid)
        .checkmark()
        .finish()
    )

    autocraft_everything = (
        chapter.quest(
            "autocraft_everything",
            "Crafting on Demand",
            "ae2:pattern_provider",
            (
                "Teach the ME network to craft a broad range of common components across multiple mods, "
                "including nested recipes that require machines rather than only crafting tables."
            ),
            2,
            0,
        )
        .depends_on(convergence)
        .checkmark()
        .finish()
    )

    cross_mod_processing = (
        chapter.quest(
            "cross_mod_processing",
            "Machines Working Together",
            "create:mechanical_arm",
            (
                "Build at least one production chain that intentionally combines machines from two or "
                "more major mods instead of keeping every technology in an isolated room."
            ),
            4,
            0,
        )
        .depends_on(autocraft_everything)
        .checkmark()
        .finish()
    )

    stocked_materials = (
        chapter.quest(
            "stocked_materials",
            "Always Keep the Essentials",
            "ae2:level_emitter",
            (
                "Use stock controls to maintain reserves of frequently consumed materials. Production "
                "should start when inventory falls and stop before storage fills with excess output."
            ),
            6,
            0,
        )
        .depends_on(cross_mod_processing)
        .checkmark()
        .finish()
    )

    remote_factory = (
        chapter.quest(
            "remote_factory",
            "Industry Beyond the Main Base",
            "create:track_station",
            (
                "Operate a remote mine, farm, reactor site, or processing facility and move its output "
                "back through trains, network storage, teleportation, or another dependable logistics system."
            ),
            8,
            0,
        )
        .depends_on(stocked_materials)
        .checkmark()
        .finish()
    )

    continuous_production = (
        chapter.quest(
            "continuous_production",
            "A Factory That Runs Unattended",
            "mekanism:ultimate_factory",
            (
                "Run a substantial automated production line through a full operating cycle without "
                "manual item transfers, hand crafting, or emergency intervention."
            ),
            10,
            0,
        )
        .depends_on(remote_factory, resilient_base)
        .checkmark()
        .finish()
    )

    signature_spell = (
        chapter.quest(
            "signature_spell",
            "Perfect a Signature Spell",
            "ars_nouveau:archmage_spell_book",
            (
                "Create and field-test a high-tier spell designed for a clear purpose: combat, movement, "
                "construction, resource gathering, or emergency survival."
            ),
            2,
            4,
        )
        .depends_on(convergence)
        .checkmark()
        .finish()
    )

    legendary_loadout = (
        chapter.quest(
            "legendary_loadout",
            "Endgame Arsenal",
            "minecraft:netherite_chestplate",
            (
                "Assemble a coherent endgame equipment set with strong affixes, useful sockets, advanced "
                "enchantments, and tools suited to the encounters you intend to face."
            ),
            4,
            4,
        )
        .depends_on(signature_spell)
        .checkmark()
        .finish()
    )

    magical_automation = (
        chapter.quest(
            "magical_automation",
            "Magic on the Production Floor",
            "ars_nouveau:spell_turret",
            (
                "Use Ars Nouveau automation in a practical system such as farming, block manipulation, "
                "transport, defense, or resource processing alongside your technological infrastructure."
            ),
            6,
            4,
        )
        .depends_on(signature_spell, cross_mod_processing)
        .checkmark()
        .finish()
    )

    field_test = (
        chapter.quest(
            "field_test",
            "Prove the Integrated Build",
            "minecraft:totem_of_undying",
            (
                "Take your complete spell and equipment loadout into a dangerous expedition or boss fight. "
                "Return with the system proven, repaired, and improved by what you learned."
            ),
            8,
            4,
        )
        .depends_on(legendary_loadout, magical_automation)
        .checkmark()
        .finish()
    )

    energy_reserve = (
        chapter.quest(
            "energy_reserve",
            "Power for the Worst Day",
            "mekanism:induction_port",
            (
                "Expand your energy storage until the base can continue operating through a generator outage, "
                "reactor shutdown, or major crafting request without immediately going dark."
            ),
            10,
            -4,
        )
        .depends_on(resilient_base)
        .checkmark()
        .finish()
    )

    network_scale = (
        chapter.quest(
            "network_scale",
            "A Network Without Bottlenecks",
            "ae2:dense_smart_cable",
            (
                "Audit channels, crafting CPUs, storage distribution, and transfer paths. Expand or split the "
                "network until normal operation no longer stalls behind a single avoidable bottleneck."
            ),
            12,
            -4,
        )
        .depends_on(energy_reserve, continuous_production)
        .checkmark()
        .finish()
    )

    reactor_reliability = (
        chapter.quest(
            "reactor_reliability",
            "Reactor Reliability Trial",
            "mekanismgenerators:fission_reactor_logic_adapter",
            (
                "Operate the nuclear power station under sustained load while verifying coolant, waste, fuel, "
                "turbine throughput, automatic shutdown behavior, and recovery after a controlled stop."
            ),
            12,
            0,
        )
        .depends_on(energy_reserve)
        .checkmark()
        .finish()
    )

    industrial_city = (
        chapter.quest(
            "industrial_city",
            "From Base to Industrial City",
            "minecraft:beacon",
            (
                "Connect multiple specialized districts with power, logistics, storage, travel, and monitoring. "
                "The result should feel like one coordinated settlement rather than scattered workshops."
            ),
            14,
            0,
        )
        .depends_on(network_scale, reactor_reliability, field_test)
        .checkmark()
        .finish()
    )

    wither = (
        chapter.quest(
            "wither",
            "Contain the Wither",
            "minecraft:nether_star",
            (
                "Defeat the Wither using the equipment, logistics, and preparation systems you built throughout "
                "the pack. Treat the Nether Star as proof that your infrastructure supports major encounters."
            ),
            10,
            5,
        )
        .depends_on(field_test)
        .advancement("minecraft:nether/summon_wither")
        .finish()
    )

    beacon = (
        chapter.quest(
            "beacon",
            "Raise a Beacon",
            "minecraft:beacon",
            (
                "Construct and activate a beacon as a permanent monument to the resources and coordination of "
                "your mature base."
            ),
            12,
            5,
        )
        .depends_on(wither)
        .advancement("minecraft:nether/create_beacon")
        .finish()
    )

    dragon = (
        chapter.quest(
            "dragon",
            "The End, Revisited",
            "minecraft:dragon_head",
            (
                "Defeat the Ender Dragon with your endgame systems behind you, then establish a dependable route "
                "for future End expeditions and resource recovery."
            ),
            14,
            5,
        )
        .depends_on(beacon, industrial_city)
        .advancement("minecraft:end/kill_dragon")
        .finish()
    )

    master_automation = (
        chapter.quest(
            "master_automation",
            "Master of Automation",
            "create:precision_mechanism",
            (
                "Complete a final audit of your automated infrastructure: raw resources enter, useful products "
                "leave, stock targets are maintained, failures are visible, and recovery is documented."
            ),
            16,
            -2,
        )
        .depends_on(industrial_city)
        .checkmark()
        .finish()
    )

    master_adventure = (
        chapter.quest(
            "master_adventure",
            "Master of Adventure",
            "minecraft:elytra",
            (
                "Prepare a permanent expedition kit, reliable long-distance travel, remote resupply, and a record "
                "of the major dimensions, structures, and challenges you conquered."
            ),
            16,
            3,
        )
        .depends_on(dragon)
        .checkmark()
        .finish()
    )

    return (
        chapter.quest(
            "immersion_complete",
            "Immersive Adventure Complete",
            "minecraft:dragon_egg",
            (
                "Your world now joins exploration, engineering, magic, storage, industry, and power into a single "
                "resilient civilization. The guided journey is complete; everything built from here is your legacy."
            ),
            18,
            0,
        )
        .depends_on(master_automation, master_adventure)
        .checkmark()
        .reward_item("minecraft:nether_star")
        .finish()
    )


__all__ = ["build_endgame"]
