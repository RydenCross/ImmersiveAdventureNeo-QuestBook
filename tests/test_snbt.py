{
	default_hide_dependency_lines: false
	default_quest_shape: ""
	filename: "welcome"
	group: ""
	id: "1B973F7802646735"
	order_index: 0
	quest_links: [ ]
	quests: [
		{
			id: "65919EFE1A013093"
			tasks: [{
				Reskillable: {
					check: 0b
					comparison: "GREATER_OR_EQUAL"
					first: 10
					mode: "SKILL_LEVEL"
					second: 20
					skill_id: "mining"
				}
				SkillsLevel: {
					category: ""
					check: 0b
					comparison: "GREATER_OR_EQUAL"
					first: 10
					mode: "TOTAL_LEVEL"
					second: 20
				}
				id: "19063B84030350A4"
				type: "checkmark"
			}]
			x: 2.0d
			y: 0.0d
		}
		{
			id: "0B231A3431AEA5B0"
			rewards: [{
				count: 16
				id: "3A96E20C0BA8EC08"
				item: {
					count: 1
					id: "minecraft:bread"
				}
				type: "item"
			}]
			tasks: [{
				Reskillable: {
					check: 0b
					comparison: "GREATER_OR_EQUAL"
					first: 10
					mode: "SKILL_LEVEL"
					second: 20
					skill_id: "mining"
				}
				SkillsLevel: {
					category: "minecraft:"
					check: 0b
					comparison: "GREATER_OR_EQUAL"
					first: 10
					mode: "TOTAL_LEVEL"
					second: 20
				}
				entity: "minecraft:zombie"
				id: "244B4B431441D77F"
				type: "kill"
				value: 1L
			}]
			x: 3.5d
			y: 0.0d
		}
		{
			id: "69EF2D1F528D7C78"
			rewards: [{
				count: 16
				id: "38CEF51882145702"
				item: {
					count: 1
					id: "minecraft:bread"
				}
				type: "item"
			}]
			tasks: [{
				Reskillable: {
					check: 0b
					comparison: "GREATER_OR_EQUAL"
					first: 10
					mode: "SKILL_LEVEL"
					second: 20
					skill_id: "mining"
				}
				SkillsLevel: {
					category: ""
					check: 0b
					comparison: "GREATER_OR_EQUAL"
					first: 10
					mode: "TOTAL_LEVEL"
					second: 20
				}
				id: "146D140AF999E6AD"
				item: { count: 1, id: "minecraft:oak_log" }
				type: "item"
			}]
			x: 5.0d
			y: 0.0d
		}
		{
			id: "5C2D2BD1A9E64A5F"
			tasks: [{
				Reskillable: {
					check: 0b
					comparison: "GREATER_OR_EQUAL"
					first: 10
					mode: "SKILL_LEVEL"
					second: 20
					skill_id: "mining"
				}
				SkillsLevel: {
					category: "minecraft:"
					check: 0b
					comparison: "GREATER_OR_EQUAL"
					first: 10
					mode: "TOTAL_LEVEL"
					second: 20
				}
				dimension: "minecraft:nether"
				id: "47BC32707686F46F"
				ignore_dimension: false
				position: [I;
					0
					0
					0
				]
				size: [I;
					1
					1
					1
				]
				type: "location"
			}]
			x: 3.5d
			y: 1.5d
		}
		{
			id: "060856FB7F815E5F"
			tasks: [{
				Reskillable: {
					check: 0b
					comparison: "GREATER_OR_EQUAL"
					first: 10
					mode: "SKILL_LEVEL"
					second: 20
					skill_id: "mining"
				}
				SkillsLevel: {
					category: "minecraft:"
					check: 0b
					comparison: "GREATER_OR_EQUAL"
					first: 10
					mode: "TOTAL_LEVEL"
					second: 20
				}
				advancement: "minecraft:story/mine_stone"
				criterion: ""
				id: "797B08761A447681"
				type: "advancement"
			}]
			x: 3.5d
			y: -1.5d
		}
	]
}
