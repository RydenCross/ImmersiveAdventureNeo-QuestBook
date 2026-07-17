from generator.builder import ChapterBuilder


def build_create_processing(create: ChapterBuilder, foundations_complete: str) -> str:
    """Add the mechanical-processing branch to the existing Create chapter."""

    millstone = (
        create.quest(
            "millstone",
            "Grinding Gears",
            "create:millstone",
            (
                "The millstone is Create's first powered processor. Feed items from above and "
                "extract the results from below or through an attached inventory."
            ),
            18,
            -4,
        )
        .depends_on(foundations_complete)
        .item("create:millstone")
        .finish()
    )

    flour = (
        create.quest(
            "wheat_flour",
            "From Grain to Flour",
            "create:wheat_flour",
            (
                "Mill wheat into flour. Processing recipes often increase output or create useful "
                "byproducts compared with ordinary crafting."
            ),
            20,
            -5,
        )
        .depends_on(millstone)
        .item("create:wheat_flour", 8)
        .finish()
    )

    press = (
        create.quest(
            "mechanical_press",
            "Apply Some Pressure",
            "create:mechanical_press",
            (
                "A mechanical press compacts items placed beneath it. A depot or belt gives the "
                "press a stable working surface."
            ),
            18,
            -2,
        )
        .depends_on(foundations_complete)
        .item("create:mechanical_press")
        .finish()
    )

    depot = (
        create.quest(
            "depot",
            "A Place to Work",
            "create:depot",
            (
                "Depots hold a single stack in the world and provide a convenient workstation for "
                "presses, deployers, funnels, and robotic arms."
            ),
            20,
            -2,
        )
        .depends_on(press)
        .item("create:depot", 2)
        .finish()
    )

    iron_sheet = (
        create.quest(
            "iron_sheet",
            "Flatten the Metal",
            "create:iron_sheet",
            "Use the mechanical press to turn iron ingots into iron sheets for advanced components.",
            22,
            -2,
        )
        .depends_on(depot)
        .item("create:iron_sheet", 8)
        .finish()
    )

    basin = (
        create.quest(
            "basin",
            "Process in Batches",
            "create:basin",
            (
                "Basins hold multiple ingredients and fluids. Machines positioned above a basin "
                "perform compacting or mixing recipes."
            ),
            18,
            0,
        )
        .depends_on(foundations_complete)
        .item("create:basin", 2)
        .finish()
    )

    compacting = (
        create.quest(
            "compacting",
            "Press into the Basin",
            "minecraft:iron_block",
            (
                "Place a mechanical press above a basin to perform compacting recipes. This setup "
                "can process recipes that a depot alone cannot handle."
            ),
            20,
            0,
        )
        .depends_on(press, basin)
        .checkmark()
        .finish()
    )

    mixer = (
        create.quest(
            "mechanical_mixer",
            "Stir Things Up",
            "create:mechanical_mixer",
            (
                "A mechanical mixer works above a basin. Some recipes require heat, while all of "
                "them need enough rotational speed to operate."
            ),
            22,
            1,
        )
        .depends_on(basin, iron_sheet)
        .item("create:mechanical_mixer")
        .finish()
    )

    whisk = (
        create.quest(
            "whisk",
            "The Business End",
            "create:whisk",
            "The whisk is the key component inside a mechanical mixer and a useful spare to keep on hand.",
            22,
            -1,
            optional=True,
        )
        .depends_on(mixer)
        .item("create:whisk")
        .finish()
    )

    blaze_burner = (
        create.quest(
            "blaze_burner",
            "Bring the Heat",
            "create:blaze_burner",
            (
                "Capture a blaze with an empty burner to create a controllable heat source. Heated "
                "basins unlock recipes that ordinary mixing cannot perform."
            ),
            24,
            1,
        )
        .depends_on(mixer)
        .item("create:blaze_burner")
        .finish()
    )

    fan = (
        create.quest(
            "encased_fan",
            "Air-Powered Processing",
            "create:encased_fan",
            (
                "An encased fan pushes or pulls air depending on rotation. Blow air through specific "
                "blocks to process entire stacks without a conventional machine interface."
            ),
            18,
            4,
        )
        .depends_on(foundations_complete)
        .item("create:encased_fan")
        .finish()
    )

    washing = (
        create.quest(
            "washing",
            "Wash Away the Impurities",
            "minecraft:water_bucket",
            (
                "Blow fan air through water to wash items. Washing crushed ores is especially useful "
                "for recovering nuggets and secondary materials."
            ),
            20,
            3,
        )
        .depends_on(fan)
        .checkmark()
        .finish()
    )

    smoking = (
        create.quest(
            "smoking",
            "Smoke on the Breeze",
            "minecraft:campfire",
            "Blow fan air through a campfire to smoke food and other compatible items in bulk.",
            20,
            5,
            optional=True,
        )
        .depends_on(fan)
        .checkmark()
        .finish()
    )

    blasting = (
        create.quest(
            "blasting",
            "A Hotter Wind",
            "minecraft:lava_bucket",
            (
                "Blow fan air through lava to bulk-blast compatible materials. Keep the lava contained "
                "so moving items cannot fall into it."
            ),
            22,
            5,
        )
        .depends_on(fan, washing)
        .checkmark()
        .finish()
    )

    crushing_wheel = (
        create.quest(
            "crushing_wheel",
            "Crushing in Earnest",
            "create:crushing_wheel",
            (
                "A matched pair of crushing wheels processes materials faster and unlocks recipes "
                "beyond the millstone. Make sure both wheels rotate inward."
            ),
            24,
            4,
        )
        .depends_on(millstone, iron_sheet, blasting)
        .item("create:crushing_wheel", 2)
        .finish()
    )

    crushed_iron = (
        create.quest(
            "crushed_iron",
            "Prepare Ore for Washing",
            "create:crushed_raw_iron",
            (
                "Crush raw iron, then wash the result. This demonstrates Create's multi-stage ore "
                "processing and the value of chaining machines together."
            ),
            26,
            4,
        )
        .depends_on(crushing_wheel, washing)
        .item("create:crushed_raw_iron", 8)
        .finish()
    )

    return (
        create.quest(
            "processing_complete",
            "A Working Processing Line",
            "create:brass_casing",
            (
                "You can now mill, press, mix, compact, crush, wash, smoke, and blast materials. "
                "The next challenge is moving items automatically between every stage."
            ),
            28,
            1,
        )
        .depends_on(flour, compacting, blaze_burner, smoking, crushed_iron, whisk)
        .checkmark()
        .reward_item("create:andesite_funnel", 4)
        .finish()
    )
