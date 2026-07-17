from generator.builder import ChapterBuilder


def build_create_logistics_and_trains(create: ChapterBuilder, automation_complete: str) -> str:
    """Add long-range logistics, contraptions, and railway progression."""

    redstone_link = (
        create.quest(
            "redstone_link",
            "Signals Without Wires",
            "create:redstone_link",
            (
                "Redstone links transmit a signal between matching frequency pairs. Use two held items "
                "to tune a channel and control distant machines without long redstone lines."
            ),
            46,
            -5,
        )
        .depends_on(automation_complete)
        .item("create:redstone_link", 2)
        .finish()
    )

    display_link = (
        create.quest(
            "display_link",
            "Put the Data on Display",
            "create:display_link",
            (
                "Display links read information from compatible blocks and send it to signs or display "
                "boards. They are useful for stock levels, station names, and factory status."
            ),
            48,
            -5,
        )
        .depends_on(redstone_link)
        .item("create:display_link")
        .finish()
    )

    display_board = (
        create.quest(
            "display_board",
            "A Factory Dashboard",
            "create:display_board",
            "Combine display boards into a larger screen and connect a display link to show live information.",
            50,
            -5,
            optional=True,
        )
        .depends_on(display_link)
        .item("create:display_board", 6)
        .finish()
    )

    portable_interface = (
        create.quest(
            "portable_storage_interface",
            "Bridge Moving and Stationary",
            "create:portable_storage_interface",
            (
                "A pair of portable storage interfaces transfers items between a moving contraption and a "
                "stationary inventory while the two interfaces are aligned."
            ),
            46,
            -2,
        )
        .depends_on(automation_complete)
        .item("create:portable_storage_interface", 2)
        .finish()
    )

    mechanical_bearing = (
        create.quest(
            "mechanical_bearing",
            "Build a Moving Machine",
            "create:mechanical_bearing",
            (
                "Mechanical bearings turn connected blocks into rotating contraptions. Use chassis and glue "
                "to control exactly which blocks become part of the structure."
            ),
            48,
            -2,
        )
        .depends_on(portable_interface)
        .item("create:mechanical_bearing")
        .finish()
    )

    super_glue = (
        create.quest(
            "super_glue",
            "Hold It Together",
            "create:super_glue",
            "Super glue binds blocks into a contraption without requiring visible chassis connections.",
            50,
            -3,
        )
        .depends_on(mechanical_bearing)
        .item("create:super_glue")
        .finish()
    )

    linear_chassis = (
        create.quest(
            "linear_chassis",
            "Define the Structure",
            "create:linear_chassis",
            (
                "Linear chassis connect rows of blocks to moving contraptions. Configure their attachment range "
                "with a wrench before assembly."
            ),
            50,
            -1,
            optional=True,
        )
        .depends_on(mechanical_bearing)
        .item("create:linear_chassis", 4)
        .finish()
    )

    logistics_complete = (
        create.quest(
            "logistics_complete",
            "Logistics at Any Scale",
            "create:portable_storage_interface",
            (
                "You can now move information, transfer cargo to contraptions, and build machines that operate "
                "beyond a fixed belt line. The railway network is the next step."
            ),
            52,
            -2,
        )
        .depends_on(display_board, super_glue, linear_chassis)
        .checkmark()
        .finish()
    )

    track = (
        create.quest(
            "track",
            "Lay the First Rails",
            "create:track",
            (
                "Create tracks curve smoothly and can climb gentle slopes. Plan wide turns and leave room for "
                "stations, signals, and future double-track expansion."
            ),
            54,
            1,
        )
        .depends_on(logistics_complete)
        .item("create:track", 32)
        .finish()
    )

    station = (
        create.quest(
            "track_station",
            "Establish a Station",
            "create:track_station",
            (
                "A track station marks a stopping point and assembles nearby train carriages. Place it beside a "
                "straight section of track with room for the entire train."
            ),
            56,
            1,
        )
        .depends_on(track)
        .item("create:track_station")
        .finish()
    )

    bogey = (
        create.quest(
            "train_bogey",
            "Wheels for the Railway",
            "create:track",
            (
                "Use the station's assembly mode and place train bogeys on the highlighted track. Build each "
                "carriage on top, then glue its blocks together."
            ),
            58,
            0,
        )
        .depends_on(station, super_glue)
        .checkmark()
        .finish()
    )

    train_controls = (
        create.quest(
            "train_controls",
            "Take the Controls",
            "create:controls",
            "Train controls allow a player or scheduled conductor to drive an assembled train.",
            58,
            2,
        )
        .depends_on(station)
        .item("create:controls")
        .finish()
    )

    assemble_train = (
        create.quest(
            "assemble_train",
            "Your First Locomotive",
            "create:track_station",
            (
                "Complete a carriage with bogeys and train controls, then use the station to assemble it into a "
                "working train."
            ),
            60,
            1,
        )
        .depends_on(bogey, train_controls)
        .checkmark()
        .reward_item("create:track", 16)
        .finish()
    )

    schedule = (
        create.quest(
            "schedule",
            "Give the Train a Plan",
            "create:schedule",
            (
                "Schedules define station stops and wait conditions. Place one in a seated conductor's hand to "
                "run a route automatically."
            ),
            62,
            2,
        )
        .depends_on(assemble_train)
        .item("create:schedule")
        .finish()
    )

    signal = (
        create.quest(
            "track_signal",
            "Keep the Line Safe",
            "create:track_signal",
            (
                "Track signals divide a railway into protected sections. Trains will wait rather than enter an "
                "occupied block, preventing collisions on shared routes."
            ),
            62,
            0,
        )
        .depends_on(assemble_train)
        .item("create:track_signal", 4)
        .finish()
    )

    observer = (
        create.quest(
            "track_observer",
            "Detect Passing Trains",
            "create:track_observer",
            (
                "Track observers emit redstone when matching trains pass. Use filters to trigger crossings, "
                "loading systems, announcements, or factory machinery."
            ),
            64,
            0,
            optional=True,
        )
        .depends_on(signal, redstone_link)
        .item("create:track_observer")
        .finish()
    )

    train_door = (
        create.quest(
            "train_door",
            "Board in Style",
            "create:train_door",
            "Train doors automatically open at stations and make passenger carriages safer and easier to use.",
            64,
            3,
            optional=True,
        )
        .depends_on(schedule)
        .item("create:train_door", 2)
        .finish()
    )

    freight = (
        create.quest(
            "automated_freight",
            "Automated Freight",
            "create:item_vault",
            (
                "Equip a train with storage, align portable storage interfaces at two stations, and use a "
                "schedule to move cargo between them automatically."
            ),
            66,
            1,
        )
        .depends_on(schedule, signal, portable_interface)
        .checkmark()
        .finish()
    )

    network = (
        create.quest(
            "rail_network",
            "A Connected Railway",
            "create:track_signal",
            (
                "Expand beyond a single route. Build at least two stations, protect shared track with signals, "
                "and give your train a repeatable schedule."
            ),
            68,
            1,
        )
        .depends_on(freight, observer, train_door)
        .checkmark()
        .finish()
    )

    complete = (
        create.quest(
            "create_complete",
            "Master of Moving Parts",
            "create:precision_mechanism",
            (
                "You have progressed from hand-cranked shafts to self-running factories and scheduled freight "
                "trains. Create's mechanical toolkit is now ready to support the rest of the modpack."
            ),
            70,
            1,
        )
        .depends_on(network)
        .checkmark()
        .reward_item("create:precision_mechanism", 2)
        .finish()
    )

    return complete
