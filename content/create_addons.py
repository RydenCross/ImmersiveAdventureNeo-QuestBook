from generator.builder import ChapterBuilder
from model import Project


def build_create_addons(project: Project, create_complete: str) -> str:
    chapter = ChapterBuilder(
        project,
        slug="12_create_addons",
        title="Create Addons",
        icon="create:brass_casing",
        description=(
            "Expand Create with electricity, diesel power, artillery, advanced railways, "
            "contraption utilities, and experimental aviation systems."
        ),
    )

    begin = (
        chapter.quest(
            "begin",
            "Beyond the Main Workshop",
            "create:wrench",
            (
                "Complete the core Create chapter, then explore the specialist addons installed in the pack. "
                "Many addon releases use different registry names, so these quests focus on building and testing systems."
            ),
            0,
            0,
        )
        .depends_on(create_complete)
        .checkmark()
        .finish()
    )

    # Create: New Age
    new_age = (
        chapter.quest(
            "new_age",
            "A New Age of Rotation",
            "minecraft:copper_block",
            "Read the Create: New Age documentation and identify how rotational force and electrical power interact.",
            2,
            -6,
        )
        .depends_on(begin)
        .checkmark()
        .finish()
    )
    generator = (
        chapter.quest(
            "new_age_generator",
            "Rotation into Electricity",
            "create:shaft",
            "Build a New Age generator setup and produce a stable electrical output from Create rotation.",
            4,
            -6,
        )
        .depends_on(new_age)
        .checkmark()
        .finish()
    )
    motor = (
        chapter.quest(
            "new_age_motor",
            "Electric Rotation",
            "create:large_cogwheel",
            "Use an electric motor to power a practical Create machine without a local water wheel or windmill.",
            6,
            -6,
        )
        .depends_on(generator)
        .checkmark()
        .finish()
    )
    new_age_grid = (
        chapter.quest(
            "new_age_grid",
            "The Electrified Factory",
            "minecraft:lightning_rod",
            "Operate a monitored electrical network that powers multiple motors or addon machines safely.",
            8,
            -6,
        )
        .depends_on(motor)
        .checkmark()
        .finish()
    )

    # Create: Diesel Generators
    diesel = (
        chapter.quest(
            "diesel",
            "Combustion Engineering",
            "minecraft:blast_furnace",
            "Begin Create: Diesel Generators and review its fuel-production and engine requirements.",
            2,
            -3,
        )
        .depends_on(begin)
        .checkmark()
        .finish()
    )
    fuel_chain = (
        chapter.quest(
            "diesel_fuel",
            "Refine the Fuel",
            "minecraft:bucket",
            "Build a complete renewable or extracted fuel-processing chain suitable for a diesel engine.",
            4,
            -3,
        )
        .depends_on(diesel)
        .checkmark()
        .finish()
    )
    diesel_engine = (
        chapter.quest(
            "diesel_engine",
            "Ignition",
            "create:flywheel",
            "Start a diesel engine and connect its rotational output to a useful factory load.",
            6,
            -3,
        )
        .depends_on(fuel_chain)
        .checkmark()
        .finish()
    )
    diesel_station = (
        chapter.quest(
            "diesel_station",
            "The Engine House",
            "minecraft:bricks",
            "Construct a dedicated engine house with fuel storage, safe routing, controls, and room for maintenance.",
            8,
            -3,
        )
        .depends_on(diesel_engine)
        .checkmark()
        .finish()
    )

    # Create: Big Cannons
    cannons = (
        chapter.quest(
            "big_cannons",
            "Heavy Engineering",
            "minecraft:iron_block",
            "Study Create: Big Cannons and prepare a safe foundry and proving ground away from important builds.",
            2,
            0,
        )
        .depends_on(begin)
        .checkmark()
        .finish()
    )
    cannon_parts = (
        chapter.quest(
            "cannon_parts",
            "Cast and Bore",
            "minecraft:anvil",
            "Produce the major components required for a functional cannon using the addon's intended manufacturing chain.",
            4,
            0,
        )
        .depends_on(cannons)
        .checkmark()
        .finish()
    )
    cannon_assembly = (
        chapter.quest(
            "cannon_assembly",
            "Assemble the Battery",
            "minecraft:dispenser",
            "Assemble, mount, and correctly load a cannon with appropriate ammunition and safety clearance.",
            6,
            0,
        )
        .depends_on(cannon_parts)
        .checkmark()
        .finish()
    )
    proof_test = (
        chapter.quest(
            "proof_test",
            "Proof Test",
            "minecraft:target",
            "Successfully test-fire the cannon at a designated target without damaging your workshop or transport network.",
            8,
            0,
        )
        .depends_on(cannon_assembly)
        .checkmark()
        .finish()
    )

    # Utility and contraption addons.
    connected = (
        chapter.quest(
            "connected",
            "Connected Construction",
            "create:andesite_casing",
            "Use Create: Connected components to improve the appearance or function of a permanent factory build.",
            2,
            3,
        )
        .depends_on(begin)
        .checkmark()
        .finish()
    )
    compact_gearbox = (
        chapter.quest(
            "compact_gearbox",
            "Compact Transmission",
            "create:gearbox",
            "Replace a bulky transmission with a Compact Gearbox solution while preserving direction and speed.",
            4,
            3,
        )
        .depends_on(connected)
        .checkmark()
        .finish()
    )
    linear_bearing = (
        chapter.quest(
            "linear_bearing",
            "Motion on a Line",
            "create:mechanical_piston",
            "Build a useful moving structure or machine based on the Linear Bearing addon.",
            6,
            3,
        )
        .depends_on(compact_gearbox)
        .checkmark()
        .finish()
    )
    contraption_terminal = (
        chapter.quest(
            "contraption_terminal",
            "Networked Contraptions",
            "ae2:terminal",
            "Access or control storage on a moving contraption with Create Contraption Terminals.",
            8,
            3,
        )
        .depends_on(linear_bearing)
        .checkmark()
        .finish()
    )
    storage_motion = (
        chapter.quest(
            "storage_in_motion",
            "Sophisticated Cargo",
            "minecraft:chest",
            "Integrate Sophisticated Storage in Motion into a train, vehicle, or mobile machine.",
            10,
            3,
        )
        .depends_on(contraption_terminal)
        .checkmark()
        .finish()
    )
    companion = (
        chapter.quest(
            "mechanical_companion",
            "A Mechanical Companion",
            "create:mechanical_arm",
            "Build and meaningfully use a Mechanical Companion in your workshop or travels.",
            12,
            3,
            optional=True,
        )
        .depends_on(storage_motion)
        .checkmark()
        .finish()
    )

    # Motors and compact power utilities.
    better_motors = (
        chapter.quest(
            "better_motors",
            "Better Motors",
            "create:rotation_speed_controller",
            "Experiment with Create Better Motors and compare its control, stress, and power requirements with standard sources.",
            10,
            -6,
        )
        .depends_on(new_age_grid)
        .checkmark()
        .finish()
    )
    motorized_line = (
        chapter.quest(
            "motorized_line",
            "Precision Motor Control",
            "create:speedometer",
            "Run an automated line from addon motors with deliberate speed control and adequate stress capacity.",
            12,
            -6,
        )
        .depends_on(better_motors)
        .checkmark()
        .finish()
    )

    # Railway addons.
    rail_addons = (
        chapter.quest(
            "rail_addons",
            "Rails with Character",
            "create:track",
            "Explore the Tracks and Bells & Whistles addons and choose components for a new railway project.",
            10,
            0,
        )
        .depends_on(proof_test, diesel_station)
        .checkmark()
        .finish()
    )
    specialty_train = (
        chapter.quest(
            "specialty_train",
            "A Specialist Train",
            "create:train_controls",
            "Build a train that visibly uses addon tracks, fittings, decorations, or functional rolling-stock components.",
            12,
            0,
        )
        .depends_on(rail_addons)
        .checkmark()
        .finish()
    )
    railway_showcase = (
        chapter.quest(
            "railway_showcase",
            "The Grand Railway Showcase",
            "create:track_station",
            "Complete a polished station or rail line demonstrating both core Create trains and installed railway addons.",
            14,
            0,
        )
        .depends_on(specialty_train)
        .checkmark()
        .finish()
    )

    # Experimental aviation stack.
    aviation = (
        chapter.quest(
            "aviation",
            "Engineering the Sky",
            "minecraft:elytra",
            "Study the Aeronautics, Propulsion, Thrusters, and Aeroworks systems before assembling a flying craft.",
            14,
            3,
        )
        .depends_on(companion, railway_showcase)
        .checkmark()
        .finish()
    )
    airframe = (
        chapter.quest(
            "airframe",
            "Build the Airframe",
            "minecraft:scaffolding",
            "Construct a balanced airframe with secure structure, accessible controls, and space for propulsion.",
            16,
            3,
        )
        .depends_on(aviation)
        .checkmark()
        .finish()
    )
    propulsion = (
        chapter.quest(
            "propulsion",
            "Propulsion Online",
            "create:propeller",
            "Install and power the appropriate propulsion or thruster system for your experimental craft.",
            18,
            3,
        )
        .depends_on(airframe)
        .checkmark()
        .finish()
    )
    flight_controls = (
        chapter.quest(
            "flight_controls",
            "Under Control",
            "minecraft:compass",
            "Configure steering, lift, thrust, and safe shutdown controls before attempting sustained flight.",
            20,
            3,
        )
        .depends_on(propulsion)
        .checkmark()
        .finish()
    )
    flight_test = (
        chapter.quest(
            "flight_test",
            "First Flight",
            "minecraft:firework_rocket",
            "Complete a controlled takeoff, flight circuit, landing, and post-flight inspection.",
            22,
            3,
        )
        .depends_on(flight_controls)
        .checkmark()
        .finish()
    )
    cargo_airship = (
        chapter.quest(
            "cargo_airship",
            "Industry Takes Flight",
            "minecraft:barrel",
            "Build a practical cargo airship or airborne work platform capable of transporting useful materials.",
            24,
            3,
        )
        .depends_on(flight_test, storage_motion)
        .checkmark()
        .finish()
    )

    return (
        chapter.quest(
            "addon_mastery",
            "Master of Expanded Engineering",
            "create:precision_mechanism",
            (
                "Demonstrate mastery of the installed Create ecosystem through electrical, combustion, railway, "
                "contraption, artillery, and aviation projects."
            ),
            26,
            0,
        )
        .depends_on(motorized_line, cargo_airship, railway_showcase, proof_test)
        .checkmark()
        .reward_item("create:brass_ingot", 16)
        .finish()
    )


__all__ = ["build_create_addons"]
