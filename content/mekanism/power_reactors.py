from generator.builder import ChapterBuilder


def build_mekanism_power_reactors(
    chapter: ChapterBuilder, processing_complete: str
) -> str:
    wind = (
        chapter.quest(
            "wind_generator",
            "Harness the High Winds",
            "mekanismgenerators:wind_generator",
            (
                "Craft a Wind Generator and place it high above the ground. Wind power is clean, "
                "passive, and an excellent bridge between early generators and reactor-scale energy."
            ),
            46,
            -6,
        )
        .depends_on(processing_complete)
        .item("mekanismgenerators:wind_generator")
        .finish()
    )

    gas_burning = (
        chapter.quest(
            "gas_burning_generator",
            "Burn Gas, Not Coal",
            "mekanismgenerators:gas_burning_generator",
            (
                "Build a Gas-Burning Generator. Hydrogen is easy to produce, while ethylene can turn "
                "a renewable farm into a powerful mid-game energy source."
            ),
            48,
            -6,
        )
        .depends_on(wind)
        .item("mekanismgenerators:gas_burning_generator")
        .finish()
    )

    ethylene = (
        chapter.quest(
            "ethylene_power",
            "A Renewable Fuel Cycle",
            "mekanism:pressurized_reaction_chamber",
            (
                "Create a renewable ethylene production chain with a Crusher, Pressurized Reaction "
                "Chamber, water, hydrogen, and farmed biomass."
            ),
            50,
            -6,
        )
        .depends_on(gas_burning)
        .checkmark()
        .finish()
    )

    advanced_cube = (
        chapter.quest(
            "advanced_energy_cube",
            "Store Industrial Power",
            "mekanism:advanced_energy_cube",
            (
                "Craft an Advanced Energy Cube. Large processing lines need enough buffered energy to "
                "survive demand spikes and generator interruptions."
            ),
            48,
            -2,
        )
        .depends_on(processing_complete)
        .item("mekanism:advanced_energy_cube")
        .finish()
    )

    induction_parts = (
        chapter.quest(
            "induction_parts",
            "Build a Multiblock Battery",
            "mekanism:induction_casing",
            (
                "Craft Induction Casings, an Induction Port, a Provider, and a Cell. These components "
                "form Mekanism's expandable long-term energy storage system."
            ),
            50,
            -2,
        )
        .depends_on(advanced_cube)
        .checkmark()
        .finish()
    )

    induction_matrix = (
        chapter.quest(
            "induction_matrix",
            "The Induction Matrix",
            "mekanism:induction_port",
            (
                "Assemble and activate an Induction Matrix. Add more cells for capacity and more "
                "providers for transfer rate as your power network grows."
            ),
            52,
            -2,
        )
        .depends_on(induction_parts)
        .checkmark()
        .finish()
    )

    hazmat = (
        chapter.quest(
            "hazmat_suit",
            "Respect Radiation",
            "mekanism:hazmat_mask",
            (
                "Prepare a complete Hazmat Suit before handling radioactive materials. Radiation can "
                "contaminate an area long after a mistake, so prevention matters more than cleanup."
            ),
            48,
            3,
        )
        .depends_on(processing_complete)
        .checkmark()
        .finish()
    )

    fissile_fuel = (
        chapter.quest(
            "fissile_fuel",
            "Prepare Fissile Fuel",
            "mekanism:fissile_fuel",
            (
                "Build the chemical chain that turns uranium into fissile fuel. Keep radioactive "
                "machines isolated, powered, and connected to secure chemical storage."
            ),
            50,
            3,
        )
        .depends_on(hazmat)
        .checkmark()
        .finish()
    )

    reactor_components = (
        chapter.quest(
            "fission_components",
            "Components of Fission",
            "mekanismgenerators:fission_reactor_casing",
            (
                "Craft Fission Reactor Casings, a Reactor Port, a Logic Adapter, Fuel Assemblies, and "
                "Control Rod Assemblies. Plan the multiblock before placing the final blocks."
            ),
            52,
            3,
        )
        .depends_on(fissile_fuel, induction_matrix)
        .checkmark()
        .finish()
    )

    reactor = (
        chapter.quest(
            "fission_reactor",
            "Contain the Reaction",
            "mekanismgenerators:fission_reactor_port",
            (
                "Assemble a valid Fission Reactor. Begin with a conservative burn rate and verify fuel, "
                "coolant, waste, and emergency shutdown paths before sustained operation."
            ),
            54,
            3,
        )
        .depends_on(reactor_components)
        .checkmark()
        .finish()
    )

    coolant = (
        chapter.quest(
            "reactor_coolant",
            "Never Run Dry",
            "mekanismgenerators:fission_reactor_logic_adapter",
            (
                "Provide a stable coolant loop and configure a reactor logic adapter for automatic "
                "shutdown. A reactor should fail safe when coolant, fuel, or waste handling stops."
            ),
            56,
            3,
        )
        .depends_on(reactor)
        .checkmark()
        .finish()
    )

    waste_barrel = (
        chapter.quest(
            "radioactive_waste_barrel",
            "Contain the Waste",
            "mekanism:radioactive_waste_barrel",
            (
                "Craft Radioactive Waste Barrels and route nuclear waste into a protected storage area. "
                "Never allow the reactor's waste output to back up."
            ),
            54,
            7,
        )
        .depends_on(reactor)
        .item("mekanism:radioactive_waste_barrel", 4)
        .finish()
    )

    polonium = (
        chapter.quest(
            "polonium",
            "Process Nuclear Waste",
            "mekanism:solar_neutron_activator",
            (
                "Use a Solar Neutron Activator to process nuclear waste into polonium. This opens the "
                "path to advanced reactor materials and late-game Mekanism technology."
            ),
            56,
            7,
        )
        .depends_on(waste_barrel)
        .item("mekanism:solar_neutron_activator")
        .finish()
    )

    turbine_parts = (
        chapter.quest(
            "turbine_parts",
            "Capture the Steam",
            "mekanismgenerators:turbine_casing",
            (
                "Craft the casings, valves, vents, rotors, blades, coils, and condensers required for an "
                "Industrial Turbine. Size it for the steam your reactor can safely produce."
            ),
            56,
            -1,
        )
        .depends_on(coolant)
        .checkmark()
        .finish()
    )

    turbine = (
        chapter.quest(
            "industrial_turbine",
            "Turn Steam into Power",
            "mekanismgenerators:turbine_valve",
            (
                "Assemble an Industrial Turbine and route reactor steam into it. Return condensed water "
                "to the coolant loop to create an efficient closed-cycle power plant."
            ),
            58,
            -1,
        )
        .depends_on(turbine_parts)
        .checkmark()
        .finish()
    )

    boiler = (
        chapter.quest(
            "thermoelectric_boiler",
            "Separate Heat from Fission",
            "mekanismgenerators:boiler_casing",
            (
                "Optionally build a Thermoelectric Boiler to move steam generation outside the reactor. "
                "A sodium-cooled design can support higher burn rates with careful engineering."
            ),
            58,
            -5,
            optional=True,
        )
        .depends_on(turbine)
        .checkmark()
        .finish()
    )

    reactor_trial = (
        chapter.quest(
            "reactor_trial",
            "A Controlled Burn",
            "mekanismgenerators:fission_reactor_logic_adapter",
            (
                "Run the reactor and turbine under load. Confirm stable coolant, empty waste output, "
                "automatic shutdown behavior, and positive net energy production."
            ),
            60,
            2,
        )
        .depends_on(turbine, polonium)
        .checkmark()
        .finish()
    )

    matrix_buffer = (
        chapter.quest(
            "matrix_buffer",
            "Buffer the Power Plant",
            "mekanism:ultimate_induction_cell",
            (
                "Connect the reactor complex to an Induction Matrix large enough to absorb full turbine "
                "output. Generation is only useful when the network can store and distribute it."
            ),
            60,
            -2,
        )
        .depends_on(induction_matrix, turbine)
        .checkmark()
        .finish()
    )

    emergency_plan = (
        chapter.quest(
            "emergency_plan",
            "Engineer for Failure",
            "mekanism:geiger_counter",
            (
                "Document and test an emergency plan: automatic SCRAM, backup coolant, waste capacity, "
                "radiation monitoring, and a safe maintenance route."
            ),
            62,
            4,
        )
        .depends_on(reactor_trial)
        .checkmark()
        .finish()
    )

    stable_reactor = (
        chapter.quest(
            "stable_reactor",
            "A Stable Nuclear Power Station",
            "mekanismgenerators:fission_reactor_casing",
            (
                "Your facility now produces fissile fuel, controls a cooled fission reaction, captures "
                "steam in a turbine, stores the output, and contains radioactive byproducts safely."
            ),
            64,
            1,
        )
        .depends_on(reactor_trial, matrix_buffer, emergency_plan)
        .checkmark()
        .reward_item("mekanism:pellet_polonium", 4)
        .finish()
    )

    return stable_reactor
