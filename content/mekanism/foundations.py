from generator.builder import ChapterBuilder
from model import Project


def build_mekanism_foundations(project: Project, ae2_complete: str) -> tuple[ChapterBuilder, str]:
    chapter = ChapterBuilder(
        project,
        slug="09_mekanism",
        title="Mekanism",
        icon="mekanism:metallurgic_infuser",
        description=(
            "Establish Mekanism power, manufacture control circuits and steel, and assemble "
            "a dependable early processing line."
        ),
    )

    begin = (
        chapter.quest(
            "begin",
            "A New Industrial Age",
            "mekanism:osmium_ingot",
            (
                "Mekanism combines power generation, configurable machines, factories, and deep "
                "resource processing. Begin by securing the metal that supports its technology."
            ),
            0,
            0,
        )
        .depends_on(ae2_complete)
        .checkmark()
        .finish()
    )

    osmium = (
        chapter.quest(
            "osmium",
            "The Blue Metal",
            "mekanism:osmium_ingot",
            "Mine and smelt Osmium, the structural metal used throughout Mekanism machines and components.",
            2,
            -2,
        )
        .depends_on(begin)
        .item("mekanism:osmium_ingot", 16)
        .finish()
    )

    heat_generator = (
        chapter.quest(
            "heat_generator",
            "Power from Heat",
            "mekanismgenerators:heat_generator",
            (
                "Craft a Heat Generator for simple early Forge Energy. Passive lava heat is modest, "
                "while burning fuel provides a stronger starting supply."
            ),
            2,
            2,
        )
        .depends_on(begin)
        .item("mekanismgenerators:heat_generator")
        .finish()
    )

    cable = (
        chapter.quest(
            "basic_universal_cable",
            "Universal Power Lines",
            "mekanism:basic_universal_cable",
            "Craft Basic Universal Cables to move Forge Energy between generators, storage, and machines.",
            4,
            2,
        )
        .depends_on(heat_generator, osmium)
        .item("mekanism:basic_universal_cable", 8)
        .finish()
    )

    infuser = (
        chapter.quest(
            "metallurgic_infuser",
            "Infuse the Metal",
            "mekanism:metallurgic_infuser",
            (
                "Build a Metallurgic Infuser. It combines metals with infusion materials such as "
                "redstone, carbon, diamond, and refined obsidian."
            ),
            4,
            -2,
        )
        .depends_on(osmium, cable)
        .item("mekanism:metallurgic_infuser")
        .finish()
    )

    basic_circuit = (
        chapter.quest(
            "basic_control_circuit",
            "Basic Control",
            "mekanism:basic_control_circuit",
            "Infuse Osmium with redstone to manufacture Basic Control Circuits for early machines.",
            6,
            -3,
        )
        .depends_on(infuser)
        .item("mekanism:basic_control_circuit", 8)
        .finish()
    )

    (
        chapter.quest(
            "enriched_redstone",
            "Concentrated Infusion",
            "mekanism:enriched_redstone",
            (
                "Create Enriched Redstone. Enriched materials provide more infusion value and reduce "
                "the amount of raw material consumed by repeated production."
            ),
            6,
            -1,
            optional=True,
        )
        .depends_on(infuser)
        .item("mekanism:enriched_redstone", 4)
        .finish()
    )

    steel = (
        chapter.quest(
            "steel_ingot",
            "Industrial Steel",
            "mekanism:ingot_steel",
            (
                "Use carbon infusion to turn iron into enriched iron and then steel dust. Smelt the "
                "result into Steel Ingots for durable Mekanism infrastructure."
            ),
            8,
            -2,
        )
        .depends_on(basic_circuit)
        .item("mekanism:ingot_steel", 8)
        .finish()
    )

    energy_tablet = (
        chapter.quest(
            "energy_tablet",
            "Portable Charge",
            "mekanism:energy_tablet",
            "Craft an Energy Tablet, a reusable power component found in energy storage and advanced machines.",
            6,
            2,
        )
        .depends_on(basic_circuit)
        .item("mekanism:energy_tablet", 2)
        .finish()
    )

    energy_cube = (
        chapter.quest(
            "basic_energy_cube",
            "Buffer the Grid",
            "mekanism:basic_energy_cube",
            (
                "Build a Basic Energy Cube to buffer production and keep machines operating when "
                "generation fluctuates. Configure its sides for input and output."
            ),
            8,
            2,
        )
        .depends_on(energy_tablet, steel)
        .item("mekanism:basic_energy_cube")
        .finish()
    )

    enrichment = (
        chapter.quest(
            "enrichment_chamber",
            "Enrich the Output",
            "mekanism:enrichment_chamber",
            (
                "Craft an Enrichment Chamber. It doubles many raw ores into dust and produces enriched "
                "infusion materials efficiently."
            ),
            10,
            -4,
        )
        .depends_on(steel, energy_cube)
        .item("mekanism:enrichment_chamber")
        .finish()
    )

    smelter = (
        chapter.quest(
            "energized_smelter",
            "Smelting without Fuel",
            "mekanism:energized_smelter",
            "Craft an Energized Smelter to process dusts and ordinary furnace recipes using network power.",
            12,
            -4,
        )
        .depends_on(enrichment)
        .item("mekanism:energized_smelter")
        .finish()
    )

    ore_doubling = (
        chapter.quest(
            "ore_doubling",
            "Two Ingots per Ore",
            "mekanism:dust_iron",
            (
                "Process a raw ore through the Enrichment Chamber and Energized Smelter. Confirm that "
                "your powered line reliably converts one raw resource into two ingots."
            ),
            14,
            -4,
        )
        .depends_on(smelter)
        .checkmark()
        .finish()
    )

    crusher = (
        chapter.quest(
            "crusher",
            "Crush and Recycle",
            "mekanism:crusher",
            (
                "Build a Crusher for bio fuel, dust conversion, and recipes that complement the "
                "Enrichment Chamber rather than replacing it."
            ),
            10,
            0,
        )
        .depends_on(steel, energy_cube)
        .item("mekanism:crusher")
        .finish()
    )

    redstone_control = (
        chapter.quest(
            "machine_configuration",
            "Sides, Slots, and Signals",
            "mekanism:configurator",
            (
                "Learn Mekanism machine side configuration, auto-eject, and redstone control. A good "
                "machine line moves items without constant manual intervention."
            ),
            12,
            0,
        )
        .depends_on(crusher, enrichment)
        .checkmark()
        .finish()
    )

    configurator = (
        chapter.quest(
            "configurator",
            "The Engineer's Multitool",
            "mekanism:configurator",
            "Craft a Configurator for changing cable modes, rotating machines, and managing Mekanism networks.",
            10,
            3,
        )
        .depends_on(steel, energy_cube)
        .item("mekanism:configurator")
        .finish()
    )

    transporter = (
        chapter.quest(
            "basic_logistical_transporter",
            "Move Items Automatically",
            "mekanism:basic_logistical_transporter",
            "Craft Basic Logistical Transporters and connect the machines in your processing line.",
            12,
            3,
        )
        .depends_on(configurator)
        .item("mekanism:basic_logistical_transporter", 8)
        .finish()
    )

    (
        chapter.quest(
            "basic_fluid_tank",
            "Prepare for Fluids",
            "mekanism:basic_fluid_tank",
            (
                "Craft a Basic Fluid Tank. Later Mekanism systems rely heavily on water, gases, slurries, "
                "and chemical processing, so fluid handling is worth establishing early."
            ),
            14,
            3,
            optional=True,
        )
        .depends_on(configurator)
        .item("mekanism:basic_fluid_tank")
        .finish()
    )

    upgrade = (
        chapter.quest(
            "speed_energy_upgrades",
            "Tune the Machines",
            "mekanism:upgrade_speed",
            (
                "Craft Speed and Energy Upgrades. Faster machines demand more power, so balance throughput "
                "against the capacity of your generator and energy cube."
            ),
            14,
            0,
        )
        .depends_on(redstone_control)
        .item("mekanism:upgrade_speed", 4)
        .item("mekanism:upgrade_energy", 4)
        .finish()
    )

    advanced_circuit = (
        chapter.quest(
            "advanced_control_circuit",
            "Advanced Control",
            "mekanism:advanced_control_circuit",
            "Upgrade Basic Control Circuits with infused alloy to unlock the next tier of Mekanism technology.",
            16,
            -2,
        )
        .depends_on(steel, enrichment)
        .item("mekanism:advanced_control_circuit", 4)
        .finish()
    )

    factory_ready = (
        chapter.quest(
            "factory_ready",
            "Ready for Factory Tiers",
            "mekanism:basic_smelting_factory",
            (
                "You now have power, storage, circuits, steel, transport, and core processing machines. "
                "The workshop is ready to scale into factories and deeper ore processing."
            ),
            18,
            0,
        )
        .depends_on(ore_doubling, transporter, upgrade, advanced_circuit)
        .checkmark()
        .reward_item("mekanism:alloy_infused", 8)
        .finish()
    )

    return chapter, factory_ready
