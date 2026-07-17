from generator.builder import ChapterBuilder
from model import Project


def build_create_foundations(project: Project, mining_complete: str) -> str:
    create = ChapterBuilder(
        project,
        slug="04_create",
        title="Create",
        icon="create:wrench",
        description=(
            "Learn rotational power, kinetic networks, and the mechanical foundations "
            "that drive Create automation."
        ),
    )

    begin = (
        create.quest(
            "begin",
            "Thinking in Motion",
            "create:wrench",
            (
                "Create is built around rotational power. Machines consume stress while "
                "shafts, gears, and power sources carry motion through a kinetic network."
            ),
            0,
            0,
        )
        .depends_on(mining_complete)
        .checkmark()
        .finish()
    )

    ponder = (
        create.quest(
            "ponder",
            "Pondering Possibilities",
            "create:goggles",
            (
                "Use Create's Ponder system whenever a component is unfamiliar. Its animated "
                "examples are often more useful than a recipe alone."
            ),
            2,
            -2,
        )
        .depends_on(begin)
        .item("create:goggles")
        .finish()
    )

    alloy = (
        create.quest(
            "andesite_alloy",
            "The Alloy That Starts It All",
            "create:andesite_alloy",
            (
                "Andesite Alloy is Create's foundational material. Keep a reserve because "
                "shafts, casings, and many machines depend on it."
            ),
            2,
            0,
        )
        .depends_on(begin)
        .item("create:andesite_alloy", 16)
        .reward_item("create:andesite_alloy", 4)
        .finish()
    )

    wrench = (
        create.quest(
            "wrench",
            "The Engineer's Best Friend",
            "create:wrench",
            (
                "A wrench rotates components, changes configuration, and safely picks up many "
                "Create blocks without breaking connected machinery."
            ),
            4,
            -2,
        )
        .depends_on(ponder, alloy)
        .item("create:wrench")
        .finish()
    )

    shaft = (
        create.quest(
            "shaft",
            "Transmit the Motion",
            "create:shaft",
            "Shafts carry rotational force in a straight line and form the backbone of kinetic networks.",
            4,
            0,
        )
        .depends_on(alloy)
        .item("create:shaft", 16)
        .finish()
    )

    cog = (
        create.quest(
            "cogwheel",
            "Teeth in the Machine",
            "create:cogwheel",
            "Cogwheels transfer rotation sideways and let nearby shafts interact.",
            6,
            -1,
        )
        .depends_on(shaft)
        .item("create:cogwheel", 8)
        .finish()
    )

    large_cog = (
        create.quest(
            "large_cogwheel",
            "Change the Pace",
            "create:large_cogwheel",
            (
                "A large cogwheel meshing with a small cogwheel changes rotational speed. "
                "Higher speed also increases the stress cost of connected machines."
            ),
            8,
            -1,
        )
        .depends_on(cog)
        .item("create:large_cogwheel", 4)
        .finish()
    )

    gearbox = (
        create.quest(
            "gearbox",
            "Turn Every Direction",
            "create:gearbox",
            "Gearboxes distribute rotation across multiple horizontal axes from one compact block.",
            8,
            -3,
        )
        .depends_on(cog)
        .item("create:gearbox", 2)
        .finish()
    )

    vertical_gearbox = (
        create.quest(
            "vertical_gearbox",
            "Take It Vertical",
            "create:vertical_gearbox",
            "Vertical gearboxes make it easier to route rotational power between floors.",
            10,
            -3,
            optional=True,
        )
        .depends_on(gearbox)
        .item("create:vertical_gearbox", 2)
        .finish()
    )

    hand_crank = (
        create.quest(
            "hand_crank",
            "Power by Hand",
            "create:hand_crank",
            (
                "A hand crank provides temporary manual rotation. It is ideal for testing a "
                "machine before committing to a permanent power source."
            ),
            6,
            1,
        )
        .depends_on(shaft)
        .item("create:hand_crank")
        .finish()
    )

    water_wheel = (
        create.quest(
            "water_wheel",
            "Harness the Current",
            "create:water_wheel",
            (
                "A water wheel provides continuous early-game power. Arrange flowing water so "
                "it pushes the paddles in a consistent direction."
            ),
            8,
            1,
        )
        .depends_on(hand_crank, large_cog)
        .item("create:water_wheel")
        .finish()
    )

    large_water_wheel = (
        create.quest(
            "large_water_wheel",
            "A Stronger Current",
            "create:large_water_wheel",
            "Large water wheels provide more stress capacity when correctly exposed to flowing water.",
            10,
            1,
        )
        .depends_on(water_wheel)
        .item("create:large_water_wheel")
        .finish()
    )

    speedometer = (
        create.quest(
            "speedometer",
            "Measure the RPM",
            "create:speedometer",
            (
                "A speedometer displays rotational speed. Use it to diagnose slow networks and "
                "avoid blindly changing gear ratios."
            ),
            10,
            -1,
        )
        .depends_on(large_cog, wrench)
        .item("create:speedometer")
        .finish()
    )

    stressometer = (
        create.quest(
            "stressometer",
            "Respect the Stress Limit",
            "create:stressometer",
            (
                "A stressometer shows how much capacity a kinetic network has and how much its "
                "machines consume. An overstressed network stops completely."
            ),
            12,
            -1,
        )
        .depends_on(speedometer, large_water_wheel)
        .item("create:stressometer")
        .finish()
    )

    clutch = (
        create.quest(
            "clutch",
            "Disconnect on Demand",
            "create:clutch",
            "A redstone-powered clutch disconnects a shaft so parts of a factory can be shut down safely.",
            12,
            1,
        )
        .depends_on(stressometer)
        .item("create:clutch", 2)
        .finish()
    )

    gearshift = (
        create.quest(
            "gearshift",
            "Reverse the Flow",
            "create:gearshift",
            "A gearshift reverses rotation when powered, making it useful for reversible machinery.",
            14,
            1,
        )
        .depends_on(clutch)
        .item("create:gearshift", 2)
        .finish()
    )

    windmill = (
        create.quest(
            "windmill",
            "Power from the Sky",
            "create:windmill_bearing",
            (
                "Build a windmill bearing and enough sails to create a scalable power source that "
                "does not depend on nearby water."
            ),
            12,
            3,
        )
        .depends_on(large_water_wheel, gearbox)
        .item("create:windmill_bearing")
        .item("create:white_sail", 8)
        .finish()
    )

    return (
        create.quest(
            "foundations_complete",
            "Ready for Mechanical Processing",
            "create:andesite_casing",
            (
                "You can now generate, route, measure, and control rotational power. The next "
                "step is using that network to automate material processing."
            ),
            16,
            0,
        )
        .depends_on(gearshift, windmill, vertical_gearbox)
        .item("create:andesite_casing", 8)
        .reward_item("create:cogwheel", 8)
        .finish()
    )
