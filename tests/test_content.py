from content import create_project
from generator.validator import ProjectValidator


def test_generated_project_is_valid() -> None:
    project = create_project()
    report = ProjectValidator().validate(project)

    assert report.is_valid
    assert len(project.chapters) == 9
    assert len(project.quests) == 349


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
    assert mining.quests[0].dependencies[0].quest_id == survival.quests[-1].ftb_id


def test_exploration_chapter_depends_on_survival_completion() -> None:
    project = create_project()
    survival = project.get_chapter("01_survival")
    exploration = project.get_chapter("03_exploration")

    assert survival is not None
    assert exploration is not None
    assert exploration.quests[0].dependencies[0].quest_id == survival.quests[-1].ftb_id


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
    assert len(ae2.quests) == 43
    assert ae2.quests[-1].title == "The Network Crafts for You"


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
    assert complete.ftb_id == ae2.quests[-1].ftb_id
    assert len(ae2.quests) == 43
