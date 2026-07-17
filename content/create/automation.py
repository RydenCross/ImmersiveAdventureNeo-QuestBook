from generator.builder import ChapterBuilder


def build_create_automation(create: ChapterBuilder, processing_complete: str) -> str:
    """Add item transport and precision automation to the Create chapter."""

    belt = (
        create.quest(
            "mechanical_belt",
            "Keep Things Moving",
            "create:belt_connector",
            (
                "Mechanical belts move items and transmit rotation between aligned shafts. "
                "Use belt connectors on two shafts to create a transport line."
            ),
            30,
            -5,
        )
        .depends_on(processing_complete)
        .item("create:belt_connector", 8)
        .finish()
    )

    funnel = (
        create.quest(
            "andesite_funnel",
            "Controlled Entry",
            "create:andesite_funnel",
            (
                "Andesite funnels insert or extract items from inventories beside belts and depots. "
                "Their arrow direction determines whether they pull or push."
            ),
            32,
            -6,
        )
        .depends_on(belt)
        .item("create:andesite_funnel", 4)
        .finish()
    )

    tunnel = (
        create.quest(
            "andesite_tunnel",
            "Route the Line",
            "create:andesite_tunnel",
            (
                "Andesite tunnels cover belts and help distribute incoming items across adjacent "
                "belt lanes without loose items spilling everywhere."
            ),
            34,
            -6,
        )
        .depends_on(funnel)
        .item("create:andesite_tunnel", 2)
        .finish()
    )

    chute = (
        create.quest(
            "chute",
            "Let Gravity Help",
            "create:chute",
            "Chutes move items vertically and connect inventories without consuming rotational power.",
            32,
            -4,
        )
        .depends_on(belt)
        .item("create:chute", 4)
        .finish()
    )

    smart_chute = (
        create.quest(
            "smart_chute",
            "Only What Belongs",
            "create:smart_chute",
            (
                "Smart chutes add filtering and redstone control to vertical item transport, making "
                "them useful for separating recipe inputs and outputs."
            ),
            34,
            -4,
        )
        .depends_on(chute)
        .item("create:smart_chute", 2)
        .finish()
    )

    brass = (
        create.quest(
            "brass_ingot",
            "Enter the Brass Age",
            "create:brass_ingot",
            (
                "Superheat a blaze burner and mix copper with zinc to produce brass. Brass unlocks "
                "Create's most precise logistics and automation components."
            ),
            30,
            -1,
        )
        .depends_on(processing_complete)
        .item("create:brass_ingot", 8)
        .finish()
    )

    brass_casing = (
        create.quest(
            "brass_casing",
            "A Precision Housing",
            "create:brass_casing",
            "Brass casings form the structural base for advanced Create machines and logistics blocks.",
            32,
            -1,
        )
        .depends_on(brass)
        .item("create:brass_casing", 4)
        .finish()
    )

    brass_funnel = (
        create.quest(
            "brass_funnel",
            "Filtered Logistics",
            "create:brass_funnel",
            (
                "Brass funnels support precise filtering and stack-size control, allowing a belt line "
                "to deliver exactly what each machine requires."
            ),
            34,
            -2,
        )
        .depends_on(brass_casing, funnel)
        .item("create:brass_funnel", 4)
        .finish()
    )

    brass_tunnel = (
        create.quest(
            "brass_tunnel",
            "Split and Sort",
            "create:brass_tunnel",
            (
                "Brass tunnels can split, synchronize, and filter belt traffic. Use them to turn one "
                "supply line into several controlled production branches."
            ),
            36,
            -2,
        )
        .depends_on(brass_funnel, tunnel)
        .item("create:brass_tunnel", 2)
        .finish()
    )

    content_observer = (
        create.quest(
            "content_observer",
            "Watch the Inventory",
            "create:content_observer",
            (
                "A content observer emits redstone when matching items pass or appear, letting a "
                "factory react to material availability."
            ),
            36,
            -4,
            optional=True,
        )
        .depends_on(brass_funnel, smart_chute)
        .item("create:content_observer")
        .finish()
    )

    stockpile_switch = (
        create.quest(
            "stockpile_switch",
            "Maintain the Stockpile",
            "create:stockpile_switch",
            (
                "A stockpile switch measures how full an attached inventory is and provides redstone "
                "control for demand-driven production."
            ),
            38,
            -4,
            optional=True,
        )
        .depends_on(content_observer)
        .item("create:stockpile_switch")
        .finish()
    )

    deployer = (
        create.quest(
            "deployer",
            "A Mechanical Hand",
            "create:deployer",
            (
                "Deployers imitate right-click interactions and can apply held items to passing "
                "components. They are essential for automated assembly."
            ),
            34,
            1,
        )
        .depends_on(brass_casing, belt)
        .item("create:deployer")
        .finish()
    )

    mechanical_saw = (
        create.quest(
            "mechanical_saw",
            "Cut to Shape",
            "create:mechanical_saw",
            (
                "Mechanical saws cut blocks and process materials on belts. Their direction and speed "
                "determine whether they cut items or harvest structures."
            ),
            32,
            3,
        )
        .depends_on(belt)
        .item("create:mechanical_saw")
        .finish()
    )

    mechanical_crafter = (
        create.quest(
            "mechanical_crafter",
            "Craft at Factory Scale",
            "create:mechanical_crafter",
            (
                "Mechanical crafters form connected crafting grids and can automate recipes of nearly "
                "any shape when their output arrows converge correctly."
            ),
            36,
            1,
        )
        .depends_on(deployer, brass_casing)
        .item("create:mechanical_crafter", 9)
        .finish()
    )

    sequenced = (
        create.quest(
            "sequenced_assembly",
            "One Step at a Time",
            "create:incomplete_precision_mechanism",
            (
                "Sequenced assembly sends an incomplete item through several operations in order. "
                "Build a loop so each component returns for its next required step."
            ),
            38,
            1,
        )
        .depends_on(deployer, mechanical_saw, mechanical_crafter)
        .item("create:incomplete_precision_mechanism")
        .finish()
    )

    precision = (
        create.quest(
            "precision_mechanism",
            "Precision Engineering",
            "create:precision_mechanism",
            (
                "Complete a precision mechanism through sequenced assembly. This component is a key "
                "gateway to advanced Create machinery."
            ),
            40,
            1,
        )
        .depends_on(sequenced)
        .item("create:precision_mechanism", 4)
        .reward_item("create:precision_mechanism")
        .finish()
    )

    mechanical_arm = (
        create.quest(
            "mechanical_arm",
            "Reach Across the Factory",
            "create:mechanical_arm",
            (
                "Mechanical arms transfer items between selected inputs and outputs. Configure every "
                "target before placing the arm to build compact routing systems."
            ),
            40,
            -2,
        )
        .depends_on(precision, brass_tunnel)
        .item("create:mechanical_arm")
        .finish()
    )

    item_vault = (
        create.quest(
            "item_vault",
            "Bulk Factory Storage",
            "create:item_vault",
            (
                "Item vaults combine into large multiblock inventories and interface cleanly with belts, "
                "funnels, and mechanical arms."
            ),
            42,
            -2,
        )
        .depends_on(mechanical_arm)
        .item("create:item_vault", 6)
        .finish()
    )

    complete = (
        create.quest(
            "automation_complete",
            "The Factory Runs Itself",
            "create:precision_mechanism",
            (
                "You can now transport, filter, route, assemble, and store items automatically. "
                "Your next machines can focus on large-scale logistics and transportation."
            ),
            44,
            0,
        )
        .depends_on(item_vault, stockpile_switch, precision)
        .checkmark()
        .reward_item("create:brass_funnel", 2)
        .finish()
    )

    return complete
