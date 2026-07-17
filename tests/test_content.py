from content import create_project
from generator.validator import ProjectValidator


def test_generated_project_is_valid() -> None:
    project = create_project()
    report = ProjectValidator().validate(project)

    assert report.is_valid
    assert len(project.chapters) == 13
    assert len(project.quests) == 556


def test_quest_ids_are_stable() -> None:
    first = create_project()
    second = create_project()

    assert [quest.ftb_id for quest in first.quests] == [quest.ftb_id for quest in second.quests]


def test_survival_chapter_depends_on_welcome_completion() -> None:
    project = create_project()
    welcome = project.get_chapter("00_welcome")
    survival = project.get_chapter("01_survival")

    assert welcome is not None
    assert survival is not None
    assert survival.quests[0].dependencies[0].quest_id == welcome.quests[-1].ftb_id


def test_mining_chapter_depends_on_survival_completion() -> None:
    project = create_project()
    survival = project.get_chapter("01_survival")
    mining = project.get_chapter("02_mining")

    assert survival is not None
    assert mining is not None
    established = next(q for q in survival.quests if q.title == "A Proper Homestead")
    assert mining.quests[0].dependencies[0].quest_id == established.ftb_id


def test_exploration_chapter_depends_on_survival_completion() -> None:
    project = create_project()
    survival = project.get_chapter("01_survival")
    exploration = project.get_chapter("03_exploration")

    assert survival is not None
    assert exploration is not None
    established = next(q for q in survival.quests if q.title == "A Proper Homestead")
    assert exploration.quests[0].dependencies[0].quest_id == established.ftb_id



def test_exploration_expansion_follows_experienced_explorer() -> None:
    project = create_project()
    exploration = project.get_chapter("03_exploration")

    assert exploration is not None
    experienced = next(q for q in exploration.quests if q.title == "Experienced Explorer")
    archaeology = next(q for q in exploration.quests if q.title == "Brush with History")
    nether = next(q for q in exploration.quests if q.title == "Into the Nether Wilds")
    mastery = next(q for q in exploration.quests if q.title == "Cartographer of Three Worlds")

    assert archaeology.dependencies[0].quest_id == experienced.ftb_id
    assert nether.dependencies[0].quest_id == experienced.ftb_id
    assert exploration.quests.index(experienced) < exploration.quests.index(mastery)
    assert all(q.optional for q in exploration.quests[exploration.quests.index(experienced) + 1 :])
    assert len(exploration.quests) == 47

def test_create_chapter_depends_on_mining_completion() -> None:
    project = create_project()
    mining = project.get_chapter("02_mining")
    create = project.get_chapter("04_create")

    assert mining is not None
    assert create is not None
    assert create.quests[0].dependencies[0].quest_id == mining.quests[-1].ftb_id
    assert len(create.quests) == 74


def test_create_processing_follows_foundations() -> None:
    project = create_project()
    create = project.get_chapter("04_create")

    assert create is not None
    foundations = next(q for q in create.quests if q.title == "Ready for Mechanical Processing")
    millstone = next(q for q in create.quests if q.title == "Grinding Gears")
    processing = next(q for q in create.quests if q.title == "A Working Processing Line")

    assert millstone.dependencies[0].quest_id == foundations.ftb_id
    assert create.quests.index(processing) < len(create.quests) - 1


def test_create_automation_follows_processing() -> None:
    project = create_project()
    create = project.get_chapter("04_create")

    assert create is not None
    processing = next(q for q in create.quests if q.title == "A Working Processing Line")
    belt = next(q for q in create.quests if q.title == "Keep Things Moving")
    complete = next(q for q in create.quests if q.title == "The Factory Runs Itself")

    assert belt.dependencies[0].quest_id == processing.ftb_id
    assert create.quests.index(complete) < len(create.quests) - 1
    assert len(create.quests) == 74


def test_create_logistics_and_trains_follow_automation() -> None:
    project = create_project()
    create = project.get_chapter("04_create")

    assert create is not None
    automation = next(q for q in create.quests if q.title == "The Factory Runs Itself")
    redstone_link = next(q for q in create.quests if q.title == "Signals Without Wires")
    railway = next(q for q in create.quests if q.title == "Master of Moving Parts")

    assert redstone_link.dependencies[0].quest_id == automation.ftb_id
    assert railway.ftb_id == create.quests[-1].ftb_id
    assert len(create.quests) == 74


def test_actually_additions_depends_on_create_completion() -> None:
    project = create_project()
    create = project.get_chapter("04_create")
    actually = project.get_chapter("05_actually_additions")

    assert create is not None
    assert actually is not None
    assert actually.quests[0].dependencies[0].quest_id == create.quests[-1].ftb_id
    assert len(actually.quests) == 58
    assert actually.quests[-1].title == "Actually Equipped"


def test_actually_additions_machines_follow_foundations() -> None:
    project = create_project()
    actually = project.get_chapter("05_actually_additions")

    assert actually is not None
    foundations = next(q for q in actually.quests if q.title == "A Reconstructed Workshop")
    crusher = next(q for q in actually.quests if q.title == "Crush the Competition")
    complete = next(q for q in actually.quests if q.title == "An Actually Automated Workshop")

    assert crusher.dependencies[0].quest_id == foundations.ftb_id
    assert actually.quests.index(complete) < len(actually.quests) - 1
    assert len(actually.quests) == 58


def test_actually_additions_tools_follow_machines() -> None:
    project = create_project()
    actually = project.get_chapter("05_actually_additions")

    assert actually is not None
    machines = next(q for q in actually.quests if q.title == "An Actually Automated Workshop")
    drill = next(q for q in actually.quests if q.title == "A Drill for Every Job")
    complete = next(q for q in actually.quests if q.title == "Actually Equipped")

    assert drill.dependencies[0].quest_id == machines.ftb_id
    assert complete.ftb_id == actually.quests[-1].ftb_id
    assert len(actually.quests) == 58


def test_ars_nouveau_depends_on_actually_additions_completion() -> None:
    project = create_project()
    actually = project.get_chapter("05_actually_additions")
    ars = project.get_chapter("06_ars_nouveau")

    assert actually is not None
    assert ars is not None
    assert ars.quests[0].dependencies[0].quest_id == actually.quests[-1].ftb_id
    assert len(ars.quests) == 41
    assert ars.quests[-1].title == "Master of Practical Spellcraft"


def test_ars_nouveau_foundations_have_workshop_progression() -> None:
    project = create_project()
    ars = project.get_chapter("06_ars_nouveau")

    assert ars is not None
    spellbook = next(q for q in ars.quests if q.title == "Your First Spellbook")
    first_spell = next(q for q in ars.quests if q.title == "Compose Your First Spell")
    apparatus = next(q for q in ars.quests if q.title == "The Enchanting Apparatus")
    complete = next(q for q in ars.quests if q.title == "An Arcane Workshop")

    assert spellbook.ftb_id in [d.quest_id for d in next(q for q in ars.quests if q.title == "Write Magic into Form").dependencies]
    assert ars.quests.index(first_spell) < ars.quests.index(apparatus)
    assert ars.quests.index(complete) < len(ars.quests) - 1


def test_ars_nouveau_spellcraft_follows_foundations() -> None:
    project = create_project()
    ars = project.get_chapter("06_ars_nouveau")

    assert ars is not None
    foundations = next(q for q in ars.quests if q.title == "An Arcane Workshop")
    apprentice = next(q for q in ars.quests if q.title == "Advance Your Studies")
    archmage = next(q for q in ars.quests if q.title == "The Archmage's Grimoire")
    complete = next(q for q in ars.quests if q.title == "Master of Practical Spellcraft")

    assert apprentice.dependencies[0].quest_id == foundations.ftb_id
    assert ars.quests.index(archmage) < ars.quests.index(complete)
    assert complete.ftb_id == ars.quests[-1].ftb_id
    assert len(ars.quests) == 41


def test_apotheosis_depends_on_ars_nouveau_completion() -> None:
    project = create_project()
    ars = project.get_chapter("06_ars_nouveau")
    apotheosis = project.get_chapter("07_apotheosis")

    assert ars is not None
    assert apotheosis is not None
    assert apotheosis.quests[0].dependencies[0].quest_id == ars.quests[-1].ftb_id
    assert len(apotheosis.quests) == 42
    assert apotheosis.quests[-1].title == "Apotheosis Mastery"


def test_apotheosis_foundations_cover_gear_gems_and_enchanting() -> None:
    project = create_project()
    apotheosis = project.get_chapter("07_apotheosis")

    assert apotheosis is not None
    salvage = next(q for q in apotheosis.quests if q.title == "Nothing Powerful Goes to Waste")
    reforge = next(q for q in apotheosis.quests if q.title == "Rewrite the Affixes")
    socket = next(q for q in apotheosis.quests if q.title == "Set the Gem")
    enchant = next(q for q in apotheosis.quests if q.title == "Beyond Vanilla Limits")
    complete = next(q for q in apotheosis.quests if q.title == "The First Apotheosis")

    assert apotheosis.quests.index(salvage) < apotheosis.quests.index(reforge)
    assert apotheosis.quests.index(reforge) < apotheosis.quests.index(socket)
    assert apotheosis.quests.index(enchant) < apotheosis.quests.index(complete)
    assert apotheosis.quests.index(complete) < len(apotheosis.quests) - 1


def test_apotheosis_advanced_progression_follows_foundations() -> None:
    project = create_project()
    apotheosis = project.get_chapter("07_apotheosis")

    assert apotheosis is not None
    foundations = next(q for q in apotheosis.quests if q.title == "The First Apotheosis")
    hunt = next(q for q in apotheosis.quests if q.title == "Hunt for Greater Power")
    infusion = next(q for q in apotheosis.quests if q.title == "Infuse Beyond Ordinary Crafting")
    complete = next(q for q in apotheosis.quests if q.title == "Apotheosis Mastery")

    assert hunt.dependencies[0].quest_id == foundations.ftb_id
    assert apotheosis.quests.index(infusion) < apotheosis.quests.index(complete)
    assert complete.ftb_id == apotheosis.quests[-1].ftb_id
    assert len(apotheosis.quests) == 42


def test_ae2_depends_on_apotheosis_completion() -> None:
    project = create_project()
    apotheosis = project.get_chapter("07_apotheosis")
    ae2 = project.get_chapter("08_ae2")

    assert apotheosis is not None
    assert ae2 is not None
    assert ae2.quests[0].dependencies[0].quest_id == apotheosis.quests[-1].ftb_id
    assert len(ae2.quests) == 63
    assert ae2.quests[-1].title == "Master of the ME Network"


def test_ae2_foundations_cover_processors_power_and_storage() -> None:
    project = create_project()
    ae2 = project.get_chapter("08_ae2")

    assert ae2 is not None
    fluix = next(q for q in ae2.quests if q.title == "Fluix Formation")
    inscriber = next(q for q in ae2.quests if q.title == "Pressing Matters")
    controller = next(q for q in ae2.quests if q.title == "The Network Core")
    drive = next(q for q in ae2.quests if q.title == "A Home for Storage Cells")
    complete = next(q for q in ae2.quests if q.title == "A Functioning ME Network")

    assert ae2.quests.index(fluix) < ae2.quests.index(inscriber)
    assert ae2.quests.index(inscriber) < ae2.quests.index(controller)
    assert ae2.quests.index(controller) < ae2.quests.index(drive)
    assert ae2.quests.index(complete) < len(ae2.quests) - 1


def test_ae2_channels_and_autocrafting_follow_foundations() -> None:
    project = create_project()
    ae2 = project.get_chapter("08_ae2")

    assert ae2 is not None
    foundations = next(q for q in ae2.quests if q.title == "A Functioning ME Network")
    channels = next(q for q in ae2.quests if q.title == "Count the Channels")
    first_craft = next(q for q in ae2.quests if q.title == "Request the First Autocraft")
    complete = next(q for q in ae2.quests if q.title == "The Network Crafts for You")

    assert channels.dependencies[0].quest_id == foundations.ftb_id
    assert ae2.quests.index(first_craft) < ae2.quests.index(complete)
    assert ae2.quests.index(complete) < len(ae2.quests) - 1
    assert len(ae2.quests) == 63


def test_ae2_advanced_storage_and_networking_follow_autocrafting() -> None:
    project = create_project()
    ae2 = project.get_chapter("08_ae2")

    assert ae2 is not None
    autocrafting = next(q for q in ae2.quests if q.title == "The Network Crafts for You")
    larger_cells = next(q for q in ae2.quests if q.title == "Storage That Scales")
    p2p = next(q for q in ae2.quests if q.title == "Tunnel the Network")
    mastery = next(q for q in ae2.quests if q.title == "Master of the ME Network")

    assert larger_cells.dependencies[0].quest_id == autocrafting.ftb_id
    assert ae2.quests.index(larger_cells) < ae2.quests.index(p2p)
    assert mastery.ftb_id == ae2.quests[-1].ftb_id
    assert len(ae2.quests) == 63


def test_mekanism_depends_on_ae2_completion() -> None:
    project = create_project()
    ae2 = project.get_chapter("08_ae2")
    mekanism = project.get_chapter("09_mekanism")

    assert ae2 is not None
    assert mekanism is not None
    assert mekanism.quests[0].dependencies[0].quest_id == ae2.quests[-1].ftb_id
    assert len(mekanism.quests) == 62
    assert mekanism.quests[-1].title == "A Stable Nuclear Power Station"


def test_mekanism_foundations_build_a_processing_line() -> None:
    project = create_project()
    mekanism = project.get_chapter("09_mekanism")

    assert mekanism is not None
    infuser = next(q for q in mekanism.quests if q.title == "Infuse the Metal")
    steel = next(q for q in mekanism.quests if q.title == "Industrial Steel")
    enrichment = next(q for q in mekanism.quests if q.title == "Enrich the Output")
    smelter = next(q for q in mekanism.quests if q.title == "Smelting without Fuel")
    complete = next(q for q in mekanism.quests if q.title == "Ready for Factory Tiers")

    assert mekanism.quests.index(infuser) < mekanism.quests.index(steel)
    assert mekanism.quests.index(steel) < mekanism.quests.index(enrichment)
    assert mekanism.quests.index(enrichment) < mekanism.quests.index(smelter)
    assert mekanism.quests.index(complete) < len(mekanism.quests) - 1


def test_mekanism_factories_and_advanced_processing_follow_foundations() -> None:
    project = create_project()
    mekanism = project.get_chapter("09_mekanism")

    assert mekanism is not None
    foundations = next(q for q in mekanism.quests if q.title == "Ready for Factory Tiers")
    factory = next(q for q in mekanism.quests if q.title == "From Machine to Factory")
    triple = next(q for q in mekanism.quests if q.title == "Three Ingots per Ore")
    five_times = next(q for q in mekanism.quests if q.title == "Five Ingots per Ore")
    mastery = next(q for q in mekanism.quests if q.title == "A Scalable Industrial Processor")

    assert factory.dependencies[0].quest_id == next(q for q in mekanism.quests if q.title == "Upgrade without Rebuilding").ftb_id
    assert next(q for q in mekanism.quests if q.title == "Upgrade without Rebuilding").dependencies[0].quest_id == foundations.ftb_id
    assert mekanism.quests.index(triple) < mekanism.quests.index(five_times)
    assert mekanism.quests.index(mastery) < len(mekanism.quests) - 1
    assert len(mekanism.quests) == 62


def test_mekanism_power_and_reactors_follow_advanced_processing() -> None:
    project = create_project()
    mekanism = project.get_chapter("09_mekanism")

    assert mekanism is not None
    processing = next(
        q for q in mekanism.quests if q.title == "A Scalable Industrial Processor"
    )
    wind = next(q for q in mekanism.quests if q.title == "Power from the Sky")
    reactor = next(q for q in mekanism.quests if q.title == "Contain the Reaction")
    complete = next(
        q for q in mekanism.quests if q.title == "A Stable Nuclear Power Station"
    )

    assert wind.dependencies[0].quest_id == processing.ftb_id
    assert mekanism.quests.index(reactor) < mekanism.quests.index(complete)
    assert complete.ftb_id == mekanism.quests[-1].ftb_id
    assert len(mekanism.quests) == 62


def test_endgame_depends_on_all_major_mastery_quests() -> None:
    project = create_project()
    endgame = project.get_chapter("10_endgame")

    assert endgame is not None
    first = endgame.quests[0]
    expected = {
        project.get_chapter("04_create").quests[-1].ftb_id,
        project.get_chapter("05_actually_additions").quests[-1].ftb_id,
        project.get_chapter("06_ars_nouveau").quests[-1].ftb_id,
        project.get_chapter("07_apotheosis").quests[-1].ftb_id,
        project.get_chapter("08_ae2").quests[-1].ftb_id,
        project.get_chapter("09_mekanism").quests[-1].ftb_id,
    }

    assert {dependency.quest_id for dependency in first.dependencies} == expected
    assert len(endgame.quests) == 24
    assert endgame.quests[-1].title == "Immersive Adventure Complete"


def test_endgame_combines_infrastructure_and_final_challenges() -> None:
    project = create_project()
    endgame = project.get_chapter("10_endgame")

    assert endgame is not None
    continuous = next(q for q in endgame.quests if q.title == "A Factory That Runs Unattended")
    city = next(q for q in endgame.quests if q.title == "From Base to Industrial City")
    dragon = next(q for q in endgame.quests if q.title == "The End, Revisited")
    complete = next(q for q in endgame.quests if q.title == "Immersive Adventure Complete")

    assert endgame.quests.index(continuous) < endgame.quests.index(city)
    assert endgame.quests.index(city) < endgame.quests.index(dragon)
    assert complete.ftb_id == endgame.quests[-1].ftb_id


def test_challenges_unlock_after_endgame_completion() -> None:
    project = create_project()
    endgame = project.get_chapter("10_endgame")
    challenges = project.get_chapter("11_challenges")

    assert endgame is not None
    assert challenges is not None
    assert challenges.quests[0].dependencies[0].quest_id == endgame.quests[-1].ftb_id
    assert len(challenges.quests) == 30
    assert challenges.quests[-1].title == "The Immersive Completionist"
    assert all(quest.optional for quest in challenges.quests)


def test_challenges_cover_factories_power_adventure_and_building() -> None:
    project = create_project()
    challenges = project.get_chapter("11_challenges")

    assert challenges is not None
    factory = next(q for q in challenges.quests if q.title == "The Megafactory")
    reactor = next(q for q in challenges.quests if q.title == "Push the Reactor")
    boss = next(q for q in challenges.quests if q.title == "Boss Rush")
    city = next(q for q in challenges.quests if q.title == "A Living City")
    completion = next(q for q in challenges.quests if q.title == "The Immersive Completionist")

    assert challenges.quests.index(factory) < challenges.quests.index(city)
    assert challenges.quests.index(reactor) < challenges.quests.index(completion)
    assert challenges.quests.index(boss) < challenges.quests.index(completion)
    assert completion.ftb_id == challenges.quests[-1].ftb_id


def test_create_addons_unlock_after_core_create() -> None:
    project = create_project()
    create = project.get_chapter("04_create")
    addons = project.get_chapter("12_create_addons")
    assert create is not None
    assert addons is not None
    assert addons.quests[0].dependencies[0].quest_id == create.quests[-1].ftb_id
    assert len(addons.quests) == 31
    assert addons.quests[-1].title == "Master of Expanded Engineering"


def test_create_addons_cover_major_installed_expansions() -> None:
    project = create_project()
    addons = project.get_chapter("12_create_addons")
    assert addons is not None
    titles = {quest.title for quest in addons.quests}
    assert "A New Age of Rotation" in titles
    assert "Combustion Engineering" in titles
    assert "Heavy Engineering" in titles
    assert "Engineering the Sky" in titles
    assert "The Grand Railway Showcase" in titles
