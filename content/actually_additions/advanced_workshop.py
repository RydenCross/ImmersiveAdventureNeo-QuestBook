from generator.builder import ChapterBuilder


def build_actually_additions_advanced_workshop(
    chapter: ChapterBuilder, utilities_complete: str
) -> str:
    """Add optional late-game power, relay, and workshop-integration challenges."""

    power_plan = chapter.quest(
        "advanced_power_plan", "Plan the Expanded Workshop", "actuallyadditions:empowered_restonia_crystal",
        "Design an expansion for your Actually Additions workshop with dedicated power generation, storage, laser-relay distribution, and automated crystal production.",
        49, -5, optional=True,
    ).depends_on(utilities_complete).checkmark().finish()

    solar = chapter.quest(
        "solar_array", "Power from the Sun", "actuallyadditions:solar_panel",
        "Build a solar array for quiet baseline generation. Route its output into storage so intermittent daylight does not interrupt the workshop.",
        51, -7, optional=True,
    ).depends_on(power_plan).checkmark().finish()

    canola_scale = chapter.quest(
        "canola_power_scale", "Scale the Canola Loop", "actuallyadditions:oil_generator",
        "Expand the renewable canola chain until it can continuously support several machines instead of serving as a demonstration line.",
        53, -7, optional=True,
    ).depends_on(solar).checkmark().finish()

    mixed_generation = chapter.quest(
        "mixed_generation", "A Diversified Grid", "actuallyadditions:advanced_coil",
        "Combine at least two Actually Additions power sources behind shared storage. A diversified grid should remain useful when one source is unavailable.",
        55, -7, optional=True,
    ).depends_on(canola_scale).checkmark().finish()

    battery_bank = chapter.quest(
        "battery_bank", "Reserve Power", "actuallyadditions:battery_box",
        "Create a larger battery reserve for portable tools and emergency machine operation. Keep charged batteries ready for field work.",
        51, -3, optional=True,
    ).depends_on(power_plan).item("actuallyadditions:battery_box").finish()

    relay_backbone = chapter.quest(
        "relay_backbone", "A Laser Relay Backbone", "actuallyadditions:laser_relay",
        "Build a structured Energy Laser Relay network connecting generation, storage, and several distant machine clusters.",
        53, -3, optional=True,
    ).depends_on(battery_bank).item("actuallyadditions:laser_relay", 4).finish()

    relay_priority = chapter.quest(
        "relay_priority", "Power Where It Matters", "actuallyadditions:laser_wrench",
        "Configure and document priorities for the relay network so critical processing remains powered before optional utility machines.",
        55, -3, optional=True,
    ).depends_on(relay_backbone).checkmark().finish()

    remote_annex = chapter.quest(
        "remote_annex", "The Remote Workshop Annex", "actuallyadditions:phantom_energyface",
        "Use laser relays and phantom interfaces to operate a machine annex away from the main workshop without a dense bundle of visible connections.",
        57, -3, optional=True,
    ).depends_on(relay_priority).checkmark().finish()

    empowered_line = chapter.quest(
        "empowered_line", "Automate Empowering", "actuallyadditions:empowerer",
        "Automate ingredient delivery and output collection around the Empowerer. The system should produce empowered crystals with minimal manual handling.",
        51, 1, optional=True,
    ).depends_on(power_plan).item("actuallyadditions:empowerer").finish()

    empowered_restonia = chapter.quest(
        "empowered_restonia", "Empowered Restonia", "actuallyadditions:empowered_restonia_crystal",
        "Produce Empowered Restonia and reserve it for advanced power and utility projects.",
        53, 0, optional=True,
    ).depends_on(empowered_line).item("actuallyadditions:empowered_restonia_crystal", 4).finish()

    empowered_palis = chapter.quest(
        "empowered_palis", "Empowered Palis", "actuallyadditions:empowered_palis_crystal",
        "Produce Empowered Palis as part of a complete advanced crystal inventory.",
        53, 2, optional=True,
    ).depends_on(empowered_line).item("actuallyadditions:empowered_palis_crystal", 4).finish()

    empowered_diamatine = chapter.quest(
        "empowered_diamatine", "Empowered Diamatine", "actuallyadditions:empowered_diamatine_crystal",
        "Produce Empowered Diamatine and keep enough available for high-value equipment or machine upgrades.",
        55, 0, optional=True,
    ).depends_on(empowered_restonia).item("actuallyadditions:empowered_diamatine_crystal", 4).finish()

    empowered_emeradic = chapter.quest(
        "empowered_emeradic", "Empowered Emeradic", "actuallyadditions:empowered_emeradic_crystal",
        "Produce Empowered Emeradic and complete the upper tier of the crystal-production line.",
        55, 2, optional=True,
    ).depends_on(empowered_palis).item("actuallyadditions:empowered_emeradic_crystal", 4).finish()

    crystal_stock = chapter.quest(
        "empowered_stockpile", "An Empowered Stockroom", "actuallyadditions:empowered_diamatine_crystal_block",
        "Maintain organized reserves of several empowered crystal types so future projects do not stall on batch crafting.",
        57, 1, optional=True,
    ).depends_on(empowered_diamatine, empowered_emeradic).checkmark().finish()

    reconstructor_cell = chapter.quest(
        "reconstructor_cell", "A Dedicated Reconstruction Cell", "actuallyadditions:atomic_reconstructor",
        "Build a safe, enclosed Atomic Reconstructor cell with controlled item input and output. Prevent stray beams from affecting nearby storage or builds.",
        51, 5, optional=True,
    ).depends_on(power_plan).item("actuallyadditions:atomic_reconstructor").finish()

    lens_library = chapter.quest(
        "lens_library", "A Lens for Every Task", "actuallyadditions:lens",
        "Collect and organize multiple Atomic Reconstructor lenses, then label their intended uses beside the reconstruction cell.",
        53, 5, optional=True,
    ).depends_on(reconstructor_cell).checkmark().finish()

    filtered_collection = chapter.quest(
        "filtered_collection_network", "Nothing Goes to Waste", "actuallyadditions:ranged_collector",
        "Deploy filtered Ranged Collectors around farms or processing areas and route their output into organized storage.",
        55, 5, optional=True,
    ).depends_on(lens_library).item("actuallyadditions:ranged_collector", 2).finish()

    phantom_network = chapter.quest(
        "phantom_network", "Interfaces without Clutter", "actuallyadditions:phantom_itemface",
        "Create a small network of Phantom Item, Energy, or Fluid interfaces that exposes remote machines from a clean service corridor.",
        57, 5, optional=True,
    ).depends_on(filtered_collection, remote_annex).checkmark().finish()

    unattended_trial = chapter.quest(
        "unattended_workshop_trial", "Leave the Workshop Running", "actuallyadditions:display_stand",
        "Run the expanded workshop unattended through a complete production cycle. Confirm that power, routing, and output storage recover without manual intervention.",
        59, 1, optional=True,
    ).depends_on(mixed_generation, crystal_stock, phantom_network).checkmark().finish()

    return chapter.quest(
        "advanced_workshop_complete", "The Actually Advanced Workshop", "actuallyadditions:empowered_emeradic_crystal_block",
        "Your workshop now combines renewable generation, reserve storage, laser distribution, empowered-crystal automation, remote interfaces, and reliable unattended operation.",
        61, 1, optional=True,
    ).depends_on(unattended_trial).checkmark().reward_item(
        "actuallyadditions:empowered_emeradic_crystal", 4
    ).finish()
