from generator.builder import ChapterBuilder
from model import Project


def build_actually_additions_foundations(project: Project, create_complete: str) -> str:
    chapter = ChapterBuilder(
        project,
        slug="05_actually_additions",
        title="Actually Additions",
        icon="actuallyadditions:atomic_reconstructor",
        description=(
            "Begin Actually Additions with crystal conversion, practical Forge Energy, "
            "and the machines that support a compact technical workshop."
        ),
    )

    begin = (
        chapter.quest(
            "begin",
            "Something Actually Different",
            "actuallyadditions:atomic_reconstructor",
            "Create taught you mechanical automation. Actually Additions introduces powered machines, laser conversion, crystals, and compact utility devices.",
            0,
            0,
        )
        .depends_on(create_complete)
        .checkmark()
        .finish()
    )

    manual = (
        chapter.quest(
            "manual",
            "The Actually Additions Manual",
            "actuallyadditions:booklet",
            "Keep the in-game manual nearby and use recipe-viewer integration whenever a machine or crystal recipe is unfamiliar.",
            2,
            -2,
        )
        .depends_on(begin)
        .item("actuallyadditions:booklet")
        .finish()
    )

    black_quartz = (
        chapter.quest(
            "black_quartz",
            "Black Quartz",
            "actuallyadditions:black_quartz",
            "Gather Black Quartz, a foundational material used throughout Actually Additions machines and components.",
            2,
            1,
        )
        .depends_on(begin)
        .item("actuallyadditions:black_quartz", 16)
        .finish()
    )

    coal_generator = (
        chapter.quest(
            "coal_generator",
            "Power from Solid Fuel",
            "actuallyadditions:coal_generator",
            "Craft a Coal Generator for dependable early Forge Energy. Any valid furnace fuel can keep a small workshop running.",
            4,
            2,
        )
        .depends_on(black_quartz)
        .item("actuallyadditions:coal_generator")
        .finish()
    )

    battery = (
        chapter.quest(
            "single_battery",
            "Energy in Your Pocket",
            "actuallyadditions:single_battery",
            "A battery stores Forge Energy for tools and machines. Charge one now so temporary power interruptions are less disruptive.",
            6,
            3,
        )
        .depends_on(coal_generator)
        .item("actuallyadditions:single_battery")
        .finish()
    )

    battery_box = (
        chapter.quest(
            "battery_box",
            "A Shared Energy Buffer",
            "actuallyadditions:battery_box",
            "Place a Battery Box between generation and machines to create a removable, visible energy buffer.",
            8,
            3,
        )
        .depends_on(battery)
        .item("actuallyadditions:battery_box")
        .finish()
    )

    reconstructor = (
        chapter.quest(
            "atomic_reconstructor",
            "Reconstruct Matter",
            "actuallyadditions:atomic_reconstructor",
            "The Atomic Reconstructor fires an energy beam that transforms dropped items. Give it power and control each pulse with redstone.",
            6,
            0,
        )
        .depends_on(manual, black_quartz, coal_generator)
        .item("actuallyadditions:atomic_reconstructor")
        .finish()
    )

    lens = (
        chapter.quest(
            "lens",
            "Focus the Beam",
            "actuallyadditions:lens",
            "Lenses modify Atomic Reconstructor behavior. Begin with the basic lens system and inspect available conversions before firing.",
            8,
            -2,
            optional=True,
        )
        .depends_on(reconstructor)
        .item("actuallyadditions:lens")
        .finish()
    )

    restonia = (
        chapter.quest(
            "restonia",
            "Restonia",
            "actuallyadditions:restonia_crystal",
            "Convert redstone into Restonia Crystals. These energized red crystals are central to coils, machines, and power components.",
            8,
            0,
        )
        .depends_on(reconstructor)
        .item("actuallyadditions:restonia_crystal", 8)
        .finish()
    )

    enori = (
        chapter.quest(
            "enori",
            "Enori",
            "actuallyadditions:enori_crystal",
            "Convert iron into Enori Crystals, a durable material used by many practical devices.",
            10,
            -1,
        )
        .depends_on(restonia)
        .item("actuallyadditions:enori_crystal", 8)
        .finish()
    )

    void = (
        chapter.quest(
            "void",
            "Void Crystal",
            "actuallyadditions:void_crystal",
            "Convert coal into Void Crystals. Their unusual properties support storage, tools, and utility blocks.",
            10,
            1,
        )
        .depends_on(restonia)
        .item("actuallyadditions:void_crystal", 8)
        .finish()
    )

    palis = (
        chapter.quest(
            "palis",
            "Palis",
            "actuallyadditions:palis_crystal",
            "Convert lapis lazuli into Palis Crystals for the next tier of Actually Additions crafting.",
            12,
            -2,
        )
        .depends_on(enori)
        .item("actuallyadditions:palis_crystal", 8)
        .finish()
    )

    diamatine = (
        chapter.quest(
            "diamatine",
            "Diamatine",
            "actuallyadditions:diamatine_crystal",
            "Convert diamonds into Diamatine Crystals. This is expensive, so verify the beam area before firing.",
            12,
            0,
        )
        .depends_on(enori, void)
        .item("actuallyadditions:diamatine_crystal", 4)
        .finish()
    )

    emeradic = (
        chapter.quest(
            "emeradic",
            "Emeradic",
            "actuallyadditions:emeradic_crystal",
            "Convert emeralds into Emeradic Crystals, one of the strongest basic crystal materials.",
            12,
            2,
            optional=True,
        )
        .depends_on(void)
        .item("actuallyadditions:emeradic_crystal", 4)
        .finish()
    )

    laser_wrench = (
        chapter.quest(
            "laser_wrench",
            "Link with Light",
            "actuallyadditions:laser_wrench",
            "The Laser Wrench links compatible relays. Use it carefully: select one endpoint, then the other.",
            10,
            4,
        )
        .depends_on(battery_box, restonia)
        .item("actuallyadditions:laser_wrench")
        .finish()
    )

    energy_relay = (
        chapter.quest(
            "energy_laser_relay",
            "Wireless Energy",
            "actuallyadditions:energy_laser_relay",
            "Energy Laser Relays move Forge Energy without long cable runs. Link a pair and confirm power reaches the destination.",
            12,
            4,
        )
        .depends_on(laser_wrench)
        .item("actuallyadditions:energy_laser_relay", 2)
        .finish()
    )

    energizer = (
        chapter.quest(
            "energizer",
            "Charge Items",
            "actuallyadditions:energizer",
            "The Energizer moves Forge Energy into compatible items, including batteries and powered tools.",
            14,
            3,
        )
        .depends_on(energy_relay, diamatine)
        .item("actuallyadditions:energizer")
        .finish()
    )

    enervator = (
        chapter.quest(
            "enervator",
            "Recover Stored Energy",
            "actuallyadditions:enervator",
            "The Enervator extracts Forge Energy from charged items and returns it to your network.",
            14,
            5,
            optional=True,
        )
        .depends_on(energizer)
        .item("actuallyadditions:enervator")
        .finish()
    )

    display_stands = (
        chapter.quest(
            "display_stands",
            "Prepare the Empowerer",
            "actuallyadditions:display_stand",
            "Craft four Display Stands. They surround the Empowerer and supply the ingredients for advanced crystal recipes.",
            14,
            -1,
        )
        .depends_on(palis, diamatine, emeradic)
        .item("actuallyadditions:display_stand", 4)
        .finish()
    )

    empowerer = (
        chapter.quest(
            "empowerer",
            "Empower the Crystals",
            "actuallyadditions:empowerer",
            "Build an Empowerer with four powered Display Stands arranged around it. This multiblock unlocks empowered crystal materials.",
            16,
            0,
        )
        .depends_on(display_stands, energy_relay)
        .item("actuallyadditions:empowerer")
        .finish()
    )

    return (
        chapter.quest(
            "foundations_complete",
            "A Reconstructed Workshop",
            "actuallyadditions:empowered_restonia_crystal",
            "You can generate, store, and move Forge Energy; reconstruct base materials; and operate the Empowerer. The advanced machines are now within reach.",
            18,
            1,
        )
        .depends_on(empowerer, energizer, restonia, enori, void, diamatine)
        .checkmark()
        .reward_item("actuallyadditions:restonia_crystal", 8)
        .finish()
    )
