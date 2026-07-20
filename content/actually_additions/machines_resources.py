from generator.builder import ChapterBuilder


def build_actually_additions_machines_resources(
    chapter: ChapterBuilder, foundations_complete: str
) -> str:
    """Add powered processing, farming, oil, and storage progression."""

    crusher = (
        chapter.quest(
            "crusher",
            "Crush the Competition",
            "actuallyadditions:crusher",
            "The Crusher processes ores and materials with Forge Energy. Use it as the first powered machine in your reconstructed workshop.",
            20,
            -4,
        )
        .depends_on(foundations_complete)
        .item("actuallyadditions:crusher")
        .finish()
    )

    double_crusher = (
        chapter.quest(
            "double_crusher",
            "Twice the Throughput",
            "actuallyadditions:double_crusher",
            "The Double Crusher runs two recipes at once. Build one when a single Crusher becomes the bottleneck in your processing line.",
            22,
            -4,
        )
        .depends_on(crusher)
        .item("actuallyadditions:double_crusher")
        .finish()
    )

    powered_furnace = (
        chapter.quest(
            "powered_furnace",
            "Smelting on Demand",
            "actuallyadditions:powered_furnace",
            "Replace fuel-based smelting with a Powered Furnace connected to your Forge Energy network.",
            20,
            -2,
        )
        .depends_on(foundations_complete)
        .item("actuallyadditions:powered_furnace")
        .finish()
    )

    processing_line = (
        chapter.quest(
            "processing_line",
            "A Powered Processing Line",
            "actuallyadditions:double_crusher",
            "Connect a Crusher or Double Crusher and a Powered Furnace to storage and power. Confirm that materials can move through both stages reliably.",
            24,
            -3,
        )
        .depends_on(double_crusher, powered_furnace)
        .checkmark()
        .finish()
    )

    farmer = (
        chapter.quest(
            "farmer",
            "Fields without Footsteps",
            "actuallyadditions:farmer",
            "The Farmer plants and harvests crops in front of itself. Supply seeds, provide power, and leave room for its working area.",
            20,
            0,
        )
        .depends_on(foundations_complete)
        .item("actuallyadditions:farmer")
        .finish()
    )

    canola = (
        chapter.quest(
            "canola",
            "A Crop with Potential",
            "actuallyadditions:canola",
            "Grow Canola as a renewable fuel crop. A steady farm will support the oil-processing branch that follows.",
            22,
            0,
        )
        .depends_on(farmer)
        .item("actuallyadditions:canola", 32)
        .finish()
    )

    canola_press = (
        chapter.quest(
            "canola_press",
            "Press the Harvest",
            "actuallyadditions:canola_press",
            "The Canola Press converts harvested Canola into oil. Keep fluid storage or piping ready before running large batches.",
            24,
            0,
        )
        .depends_on(canola)
        .item("actuallyadditions:canola_press")
        .finish()
    )

    fermenting_barrel = (
        chapter.quest(
            "fermenting_barrel",
            "Refine the Oil",
            "actuallyadditions:fermenting_barrel",
            "Use a Fermenting Barrel to refine pressed Canola Oil into a more useful fuel product.",
            26,
            0,
        )
        .depends_on(canola_press)
        .item("actuallyadditions:fermenting_barrel")
        .finish()
    )

    oil_generator = (
        chapter.quest(
            "oil_generator",
            "Power from the Fields",
            "actuallyadditions:oil_generator",
            "Burn refined oil in an Oil Generator. This turns an automated crop farm into renewable Forge Energy.",
            28,
            0,
        )
        .depends_on(fermenting_barrel)
        .item("actuallyadditions:oil_generator")
        .finish()
    )

    renewable_power = (
        chapter.quest(
            "renewable_power",
            "The Canola Power Loop",
            "actuallyadditions:oil_generator",
            "Automate Canola harvesting, pressing, fermentation, and oil generation so the system can sustain itself with minimal attention.",
            30,
            0,
        )
        .depends_on(oil_generator, farmer)
        .checkmark()
        .finish()
    )

    storage_crate = (
        chapter.quest(
            "storage_crate",
            "More than a Chest",
            "actuallyadditions:storage_crate",
            "Storage Crates hold large quantities in a compact block and make excellent buffers between machines.",
            20,
            3,
        )
        .depends_on(foundations_complete)
        .item("actuallyadditions:storage_crate", 2)
        .finish()
    )

    medium_crate = (
        chapter.quest(
            "medium_storage_crate",
            "Expand the Buffer",
            "actuallyadditions:medium_storage_crate",
            "Upgrade to a Medium Storage Crate when the first tier can no longer absorb production spikes.",
            22,
            3,
        )
        .depends_on(storage_crate)
        .item("actuallyadditions:medium_storage_crate")
        .finish()
    )

    large_crate = (
        chapter.quest(
            "large_storage_crate",
            "Warehouse in a Block",
            "actuallyadditions:large_storage_crate",
            "The Large Storage Crate provides a substantial inventory for centralized processing and bulk resources.",
            24,
            3,
        )
        .depends_on(medium_crate)
        .item("actuallyadditions:large_storage_crate")
        .finish()
    )

    item_interface = (
        chapter.quest(
            "item_interface",
            "One Face, Many Inventories",
            "actuallyadditions:item_interface",
            "An Item Interface exposes a connected storage network through one convenient access point. Use it to simplify machine inputs and outputs.",
            26,
            3,
        )
        .depends_on(large_crate)
        .item("actuallyadditions:item_interface")
        .finish()
    )

    breaker = (
        chapter.quest(
            "breaker",
            "Break on Command",
            "actuallyadditions:breaker",
            "The Breaker destroys blocks directly in front of it when triggered, allowing simple automated harvesting and cobblestone systems.",
            22,
            6,
        )
        .depends_on(storage_crate)
        .item("actuallyadditions:breaker")
        .finish()
    )

    placer = (
        chapter.quest(
            "placer",
            "Place on Command",
            "actuallyadditions:placer",
            "The Placer inserts blocks into the world. Pair it with a Breaker for repeatable block-processing contraptions.",
            24,
            6,
        )
        .depends_on(breaker)
        .item("actuallyadditions:placer")
        .finish()
    )

    fluid_collector = (
        chapter.quest(
            "fluid_collector",
            "Collect the Flow",
            "actuallyadditions:fluid_collector",
            "The Fluid Collector gathers source blocks in front of it. Use tanks or pipes so collected fluid always has somewhere to go.",
            26,
            6,
        )
        .depends_on(placer)
        .item("actuallyadditions:fluid_collector")
        .finish()
    )

    fluid_placer = (
        chapter.quest(
            "fluid_placer",
            "Control the Flow",
            "actuallyadditions:fluid_placer",
            "The Fluid Placer deploys stored fluids into the world, completing a useful pair for fluid automation.",
            28,
            6,
        )
        .depends_on(fluid_collector)
        .item("actuallyadditions:fluid_placer")
        .finish()
    )

    return (
        chapter.quest(
            "machines_complete",
            "An Actually Automated Workshop",
            "actuallyadditions:double_crusher",
            "Your workshop can now process resources, farm renewable fuel, buffer large inventories, and interact with blocks and fluids automatically.",
            32,
            2,
        )
        .depends_on(processing_line, renewable_power, item_interface, fluid_placer)
        .checkmark()
        .reward_item("actuallyadditions:empowered_restonia_crystal", 4)
        .finish()
    )
