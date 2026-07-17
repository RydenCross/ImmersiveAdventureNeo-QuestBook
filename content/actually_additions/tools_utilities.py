from generator.builder import ChapterBuilder


def build_actually_additions_tools_utilities(
    chapter: ChapterBuilder, machines_complete: str
) -> str:
    """Add portable tools, remote interfaces, and utility-device progression."""

    drill = chapter.quest(
        "drill", "A Drill for Every Job", "actuallyadditions:drill_light_blue",
        "Build an Actually Additions Drill as a rechargeable alternative to ordinary mining tools. Charge it in an Energizer before heading underground.",
        34, -5,
    ).depends_on(machines_complete).item("actuallyadditions:drill_light_blue").finish()

    speed_one = chapter.quest(
        "drill_speed_1", "Spin It Faster", "actuallyadditions:drill_speed_1",
        "Install the first Speed Augment to improve the Drill's mining speed. Augments trade additional energy use for stronger performance.",
        36, -5,
    ).depends_on(drill).item("actuallyadditions:drill_speed_1").finish()

    speed_two = chapter.quest(
        "drill_speed_2", "High-Speed Excavation", "actuallyadditions:drill_speed_2",
        "Upgrade the Drill with a second-tier Speed Augment and make sure your portable energy supply can support the increased demand.",
        38, -5,
    ).depends_on(speed_one).item("actuallyadditions:drill_speed_2").finish()

    three_by_three = chapter.quest(
        "drill_three_by_three", "Clear a Wider Tunnel", "actuallyadditions:drill_size_3",
        "A Size Augment lets the Drill clear a wider area at once. Use it carefully around valuable blocks and machine rooms.",
        40, -5,
    ).depends_on(speed_two).item("actuallyadditions:drill_size_3").finish()

    fortune = chapter.quest(
        "drill_fortune", "Fortune on Demand", "actuallyadditions:drill_fortune",
        "Add a Fortune Augment for ore harvesting. Keep a second configuration available when precise block collection matters more than extra drops.",
        42, -6,
    ).depends_on(three_by_three).item("actuallyadditions:drill_fortune").finish()

    silk = chapter.quest(
        "drill_silk_touch", "A Delicate Touch", "actuallyadditions:drill_silk_touch",
        "Create a Silk Touch Augment for clean collection of fragile or otherwise altered blocks. Swap augments to match the task at hand.",
        42, -4,
    ).depends_on(three_by_three).item("actuallyadditions:drill_silk_touch").finish()

    drill_complete = chapter.quest(
        "drill_complete", "The Modular Miner", "actuallyadditions:drill_light_blue",
        "Prepare a charged Drill with speed, size, and specialized harvesting options. You now have a configurable tool for large building and mining projects.",
        44, -5,
    ).depends_on(fortune, silk).checkmark().finish()

    wings = chapter.quest(
        "wings_of_the_bats", "Borrowed Wings", "actuallyadditions:wings_of_the_bats",
        "Wings of the Bats provide a rare mobility utility. Use them responsibly and keep a safe landing plan whenever temporary flight is involved.",
        35, -1,
        optional=True,
    ).depends_on(machines_complete).item("actuallyadditions:wings_of_the_bats").finish()

    player_interface = chapter.quest(
        "player_interface", "Reach the Player", "actuallyadditions:player_interface",
        "A Player Interface allows automation to interact with a linked player's inventory. Treat it as a powerful convenience block and secure it appropriately.",
        35, 1,
    ).depends_on(machines_complete).item("actuallyadditions:player_interface").finish()

    phantomface = chapter.quest(
        "phantomface", "An Inventory at a Distance", "actuallyadditions:phantom_itemface",
        "A Phantom Itemface exposes a remote inventory from another location. Link it carefully and use it to simplify crowded machine layouts.",
        37, 1,
    ).depends_on(player_interface).item("actuallyadditions:phantom_itemface").finish()

    phantom_energy = chapter.quest(
        "phantom_energyface", "Remote Power Access", "actuallyadditions:phantom_energyface",
        "Use a Phantom Energyface to expose a distant energy connection without running a visible cable through the entire build.",
        39, 0,
    ).depends_on(phantomface).item("actuallyadditions:phantom_energyface").finish()

    phantom_liquid = chapter.quest(
        "phantom_liquiface", "Remote Fluid Access", "actuallyadditions:phantom_liquiface",
        "A Phantom Liquiface provides the same remote-access concept for fluid handlers and tanks.",
        39, 2,
    ).depends_on(phantomface).item("actuallyadditions:phantom_liquiface").finish()

    ranged_collector = chapter.quest(
        "ranged_collector", "Gather from Afar", "actuallyadditions:ranged_collector",
        "The Ranged Collector pulls nearby dropped items into its inventory. Add filters so it gathers only the materials your system expects.",
        41, 1,
    ).depends_on(phantom_energy, phantom_liquid).item("actuallyadditions:ranged_collector").finish()

    item_filter = chapter.quest(
        "item_filter", "Collect with Precision", "actuallyadditions:item_filter",
        "Configure an Item Filter and apply it to a Ranged Collector or another compatible device to prevent unwanted items from clogging automation.",
        43, 1,
    ).depends_on(ranged_collector).item("actuallyadditions:item_filter").finish()

    teleport_staff = chapter.quest(
        "teleport_staff", "A Short Step through Space", "actuallyadditions:teleport_staff",
        "The Teleport Staff converts stored energy into short-range movement. Keep it charged as a utility tool for construction and exploration.",
        37, 5,
        optional=True,
    ).depends_on(machines_complete).item("actuallyadditions:teleport_staff").finish()

    hand_filler = chapter.quest(
        "hand_filler", "Fill the Gaps", "actuallyadditions:handheld_filler",
        "The Handheld Filler places blocks across an area using materials from your inventory. It is especially useful for floors, walls, and repetitive construction.",
        39, 5,
    ).depends_on(teleport_staff).item("actuallyadditions:handheld_filler").finish()

    coffee_machine = chapter.quest(
        "coffee_machine", "Industrial Refreshment", "actuallyadditions:coffee_machine",
        "Build a Coffee Machine and experiment with its ingredients. Even an automated workshop benefits from a well-supplied break room.",
        41, 5,
        optional=True,
    ).depends_on(hand_filler).item("actuallyadditions:coffee_machine").finish()

    return chapter.quest(
        "utilities_complete", "Actually Equipped", "actuallyadditions:drill_light_blue",
        "You have combined configurable tools, remote interfaces, filtered collection, and portable utilities into a flexible engineering toolkit.",
        46, 1,
    ).depends_on(drill_complete, item_filter, hand_filler).checkmark().reward_item(
        "actuallyadditions:empowered_diamatine_crystal", 4
    ).finish()
