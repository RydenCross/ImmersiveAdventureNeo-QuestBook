from generator.builder import ChapterBuilder
from model import Project


def build_ae2_foundations(project: Project, apotheosis_complete: str) -> tuple[ChapterBuilder, str]:
    chapter = ChapterBuilder(
        project,
        slug="08_ae2",
        title="Applied Energistics 2",
        icon="ae2:controller",
        description=(
            "Build the materials, processors, power infrastructure, and storage components "
            "needed for your first dependable ME network."
        ),
    )

    begin = (
        chapter.quest(
            "begin",
            "Matter, Energy, and Organization",
            "ae2:certus_quartz_crystal",
            (
                "Applied Energistics 2 replaces sprawling storage rooms with a digital ME network. "
                "Begin by gathering the quartz materials that form the basis of the system."
            ),
            0,
            0,
        )
        .depends_on(apotheosis_complete)
        .checkmark()
        .finish()
    )

    certus = (
        chapter.quest(
            "certus_quartz",
            "Certus Quartz",
            "ae2:certus_quartz_crystal",
            "Collect Certus Quartz crystals for AE2 components, processors, and storage parts.",
            2,
            -2,
        )
        .depends_on(begin)
        .item("ae2:certus_quartz_crystal", 16)
        .finish()
    )

    charged = (
        chapter.quest(
            "charged_certus",
            "A Charged Discovery",
            "ae2:charged_certus_quartz_crystal",
            "Obtain Charged Certus Quartz. It is essential for producing Fluix Crystals.",
            4,
            -2,
        )
        .depends_on(certus)
        .item("ae2:charged_certus_quartz_crystal", 4)
        .finish()
    )

    fluix = (
        chapter.quest(
            "fluix_crystal",
            "Fluix Formation",
            "ae2:fluix_crystal",
            (
                "Create Fluix Crystals by combining charged quartz, redstone, and Nether Quartz. "
                "Fluix connects power, storage, and network components throughout AE2."
            ),
            6,
            -2,
        )
        .depends_on(charged)
        .item("ae2:fluix_crystal", 8)
        .finish()
    )

    charger = (
        chapter.quest(
            "charger",
            "Charge on Demand",
            "ae2:charger",
            "Craft a Charger so ordinary Certus Quartz can be converted into charged quartz reliably.",
            6,
            -4,
        )
        .depends_on(charged)
        .item("ae2:charger")
        .finish()
    )

    quartz_fiber = (
        chapter.quest(
            "quartz_fiber",
            "Carry Power, Not Channels",
            "ae2:quartz_fiber",
            (
                "Craft Quartz Fiber. It transfers AE power without carrying network channels, making it "
                "useful for isolated power links and network design."
            ),
            8,
            -4,
        )
        .depends_on(fluix)
        .item("ae2:quartz_fiber", 4)
        .finish()
    )

    energy_acceptor = (
        chapter.quest(
            "energy_acceptor",
            "Power into AE",
            "ae2:energy_acceptor",
            "Craft an Energy Acceptor to convert Forge Energy into AE power for your network.",
            10,
            -4,
        )
        .depends_on(quartz_fiber)
        .item("ae2:energy_acceptor")
        .finish()
    )

    energy_cell = (
        chapter.quest(
            "energy_cell",
            "Keep the Network Alive",
            "ae2:energy_cell",
            "Add an Energy Cell so brief power interruptions do not immediately shut down the network.",
            12,
            -4,
        )
        .depends_on(energy_acceptor)
        .item("ae2:energy_cell")
        .finish()
    )

    inscriber = (
        chapter.quest(
            "inscriber",
            "Pressing Matters",
            "ae2:inscriber",
            "Craft an Inscriber, the machine used to manufacture printed circuits and processors.",
            8,
            0,
        )
        .depends_on(fluix)
        .item("ae2:inscriber")
        .finish()
    )

    presses = (
        chapter.quest(
            "processor_presses",
            "The Four Presses",
            "ae2:calculation_processor_press",
            (
                "Collect the Inscriber presses needed for silicon, logic, calculation, and engineering "
                "processor production."
            ),
            10,
            0,
        )
        .depends_on(inscriber)
        .checkmark()
        .finish()
    )

    silicon = (
        chapter.quest(
            "printed_silicon",
            "Printed Silicon",
            "ae2:printed_silicon",
            "Use the Silicon Press to create Printed Silicon for every processor tier.",
            12,
            -1.5,
        )
        .depends_on(presses)
        .item("ae2:printed_silicon", 8)
        .finish()
    )

    logic = (
        chapter.quest(
            "logic_processor",
            "Logic Processor",
            "ae2:logic_processor",
            "Manufacture Logic Processors for common network machines and terminals.",
            14,
            -2.5,
        )
        .depends_on(silicon)
        .item("ae2:logic_processor", 4)
        .finish()
    )

    calculation = (
        chapter.quest(
            "calculation_processor",
            "Calculation Processor",
            "ae2:calculation_processor",
            "Manufacture Calculation Processors for storage components and advanced network functions.",
            14,
            0,
        )
        .depends_on(silicon)
        .item("ae2:calculation_processor", 4)
        .finish()
    )

    engineering = (
        chapter.quest(
            "engineering_processor",
            "Engineering Processor",
            "ae2:engineering_processor",
            "Manufacture Engineering Processors for controllers, drives, and high-tier infrastructure.",
            14,
            2.5,
        )
        .depends_on(silicon)
        .item("ae2:engineering_processor", 4)
        .finish()
    )

    controller = (
        chapter.quest(
            "controller",
            "The Network Core",
            "ae2:controller",
            (
                "Craft an ME Controller. Small networks can operate without one, but a controller "
                "provides channel capacity and becomes the core of larger systems."
            ),
            16,
            1,
        )
        .depends_on(logic, calculation, engineering, energy_cell)
        .item("ae2:controller")
        .finish()
    )

    cable = (
        chapter.quest(
            "fluix_cable",
            "Connect the Network",
            "ae2:fluix_glass_cable",
            "Craft Fluix Glass Cable to carry power, channels, and data between ME devices.",
            18,
            -2,
        )
        .depends_on(controller)
        .item("ae2:fluix_glass_cable", 8)
        .finish()
    )

    terminal = (
        chapter.quest(
            "terminal",
            "A Window into Storage",
            "ae2:terminal",
            "Craft an ME Terminal to view and withdraw items stored on the network.",
            20,
            -2,
        )
        .depends_on(cable)
        .item("ae2:terminal")
        .finish()
    )

    crafting_terminal = (
        chapter.quest(
            "crafting_terminal",
            "Craft from the Network",
            "ae2:crafting_terminal",
            "Upgrade to an ME Crafting Terminal so stored items can be used directly in crafting recipes.",
            22,
            -2,
        )
        .depends_on(terminal)
        .item("ae2:crafting_terminal")
        .finish()
    )

    drive = (
        chapter.quest(
            "drive",
            "A Home for Storage Cells",
            "ae2:drive",
            "Craft an ME Drive to hold multiple storage cells in a compact, networked block.",
            18,
            2,
        )
        .depends_on(controller)
        .item("ae2:drive")
        .finish()
    )

    cell_component = (
        chapter.quest(
            "cell_component",
            "Build the Capacity",
            "ae2:cell_component_1k",
            "Craft a 1k ME Storage Component, the core used inside your first item storage cell.",
            20,
            2,
        )
        .depends_on(drive, calculation)
        .item("ae2:cell_component_1k")
        .finish()
    )

    storage_cell = (
        chapter.quest(
            "storage_cell",
            "Your First Digital Storage",
            "ae2:item_storage_cell_1k",
            "Assemble a 1k ME Item Storage Cell and install it in the ME Drive.",
            22,
            2,
        )
        .depends_on(cell_component)
        .item("ae2:item_storage_cell_1k")
        .finish()
    )

    interface = (
        chapter.quest(
            "storage_bus",
            "Connect Existing Storage",
            "ae2:storage_bus",
            (
                "Craft a Storage Bus to expose a chest, drawer, or other inventory to the ME network. "
                "This lets digital and conventional storage work together."
            ),
            22,
            4,
            optional=True,
        )
        .depends_on(cable)
        .item("ae2:storage_bus")
        .finish()
    )

    complete = (
        chapter.quest(
            "first_network",
            "A Functioning ME Network",
            "ae2:crafting_terminal",
            (
                "Power a network containing storage, a drive, at least one storage cell, and a terminal. "
                "You now have the foundation for channels, autocrafting, and advanced logistics."
            ),
            24,
            0,
        )
        .depends_on(crafting_terminal, storage_cell)
        .checkmark()
        .reward_item("minecraft:redstone", 32)
        .finish()
    )

    return chapter, complete
