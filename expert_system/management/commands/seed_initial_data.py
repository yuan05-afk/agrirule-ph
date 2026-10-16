from django.core.management.base import BaseCommand

from expert_system.models import ConsultationChoices, Crop, Rule


CROPS = [
    {
        'name': 'Rice',
        'category': Crop.Category.STAPLES_ROOT,
        'description': 'Major staple cereal crop requiring strong water support.',
        'planting_note': 'Best in puddled fields with reliable irrigation during wet periods.',
        'avoid_note': 'Avoid when water is low or irrigation is not available.',
        'profile': {'season': 'wet', 'soil': 'clay', 'water': 'high', 'farm': 'irrigated', 'pref': 'staple', 'bad_water': 'low'},
    },
    {
        'name': 'Yellow Corn',
        'category': Crop.Category.STAPLES_ROOT,
        'description': 'Versatile cereal crop adaptable to many field conditions.',
        'planting_note': 'Use good seed spacing and maintain moderate moisture during tasseling.',
        'avoid_note': 'Avoid prolonged flooding or very high standing water.',
        'profile': {'season': 'dry', 'soil': 'silt', 'water': 'moderate', 'farm': 'rainfed', 'pref': 'staple', 'bad_water': 'high'},
    },
    {
        'name': 'Cassava',
        'category': Crop.Category.STAPLES_ROOT,
        'description': 'Drought-tolerant root crop suitable for low-input systems.',
        'planting_note': 'Use healthy cuttings and weed early in the first month.',
        'avoid_note': 'Avoid waterlogged soils for long periods.',
        'profile': {'season': 'dry', 'soil': 'sandy', 'water': 'low', 'farm': 'rainfed', 'pref': 'resilient', 'bad_water': 'high'},
    },
    {
        'name': 'Sweet Potato (Camote)',
        'category': Crop.Category.STAPLES_ROOT,
        'description': 'Short-cycle root crop with strong tolerance to variable moisture.',
        'planting_note': 'Plant on raised beds and keep vines healthy during establishment.',
        'avoid_note': 'Avoid persistent flooding and compacted soils.',
        'profile': {'season': 'dry', 'soil': 'sandy', 'water': 'low', 'farm': 'rainfed', 'pref': 'resilient', 'bad_water': 'high'},
    },
    {
        'name': 'Mungbean',
        'category': Crop.Category.STAPLES_ROOT,
        'description': 'Legume crop suited to dry windows and low-input farms.',
        'planting_note': 'Use well-drained fields and avoid planting during heavy rainfall peaks.',
        'avoid_note': 'Avoid saturated fields and prolonged rainy spells.',
        'profile': {'season': 'dry', 'soil': 'loam', 'water': 'low', 'farm': 'rainfed', 'pref': 'resilient', 'bad_water': 'high'},
    },
    {
        'name': 'Peanut',
        'category': Crop.Category.STAPLES_ROOT,
        'description': 'Nitrogen-fixing legume preferring lighter, well-drained soils.',
        'planting_note': 'Maintain loose topsoil for proper pod development.',
        'avoid_note': 'Avoid heavy clay with poor drainage.',
        'profile': {'season': 'dry', 'soil': 'sandy', 'water': 'moderate', 'farm': 'rainfed', 'pref': 'resilient', 'bad_water': 'high'},
    },
    {
        'name': 'Soybean',
        'category': Crop.Category.STAPLES_ROOT,
        'description': 'Protein-rich legume suitable for moderate moisture and neutral pH.',
        'planting_note': 'Best with neutral soil and moderate rainfall.',
        'avoid_note': 'Avoid strongly acidic and flooded conditions.',
        'profile': {'season': 'dry', 'soil': 'loam', 'water': 'moderate', 'farm': 'irrigated', 'pref': 'staple', 'bad_water': 'high'},
    },
    {
        'name': 'Coconut',
        'category': Crop.Category.INDUSTRIAL_PERENNIAL,
        'description': 'Perennial tree crop with broad adaptation in tropical systems.',
        'planting_note': 'Provide spacing and maintain weed-free circles at establishment.',
        'avoid_note': 'Avoid very dry sites without supplemental moisture.',
        'profile': {'season': 'wet', 'soil': 'silt', 'water': 'moderate', 'farm': 'rainfed', 'pref': 'resilient', 'bad_water': 'low'},
    },
    {
        'name': 'Coffee',
        'category': Crop.Category.INDUSTRIAL_PERENNIAL,
        'description': 'High-value perennial requiring good moisture and drainage balance.',
        'planting_note': 'Use shade management and mulch in early growth phases.',
        'avoid_note': 'Avoid severely dry and highly alkaline conditions.',
        'profile': {'season': 'wet', 'soil': 'loam', 'water': 'moderate', 'farm': 'rainfed', 'pref': 'resilient', 'bad_water': 'low'},
    },
    {
        'name': 'Cacao',
        'category': Crop.Category.INDUSTRIAL_PERENNIAL,
        'description': 'Perennial crop needing humid conditions and regular moisture.',
        'planting_note': 'Maintain shade and consistent soil moisture.',
        'avoid_note': 'Avoid prolonged dry stress.',
        'profile': {'season': 'wet', 'soil': 'loam', 'water': 'high', 'farm': 'rainfed', 'pref': 'resilient', 'bad_water': 'low'},
    },
    {
        'name': 'Abaca',
        'category': Crop.Category.INDUSTRIAL_PERENNIAL,
        'description': 'Fiber crop thriving in humid tropical conditions.',
        'planting_note': 'Good moisture and partial shade improve stand vigor.',
        'avoid_note': 'Avoid dry areas without rainfall support.',
        'profile': {'season': 'wet', 'soil': 'loam', 'water': 'high', 'farm': 'rainfed', 'pref': 'resilient', 'bad_water': 'low'},
    },
    {
        'name': 'Rubber',
        'category': Crop.Category.INDUSTRIAL_PERENNIAL,
        'description': 'Long-term plantation crop for suitable perennial systems.',
        'planting_note': 'Choose well-drained sites and maintain weed control in early years.',
        'avoid_note': 'Avoid shallow, dry, and drought-prone soils.',
        'profile': {'season': 'wet', 'soil': 'silt', 'water': 'moderate', 'farm': 'rainfed', 'pref': 'resilient', 'bad_water': 'low'},
    },
    {
        'name': 'Sugarcane',
        'category': Crop.Category.INDUSTRIAL_PERENNIAL,
        'description': 'Commercial cane crop requiring open fields and medium to high resources.',
        'planting_note': 'Use clean seed cane and maintain fertility for ratoon success.',
        'avoid_note': 'Avoid very low water and nutrient-deprived sites.',
        'profile': {'season': 'dry', 'soil': 'silt', 'water': 'moderate', 'farm': 'irrigated', 'pref': 'staple', 'bad_water': 'low'},
    },
    {
        'name': 'Banana',
        'category': Crop.Category.FRUIT,
        'description': 'Tropical fruit crop suited to moderate to high moisture.',
        'planting_note': 'Maintain sucker selection and wind protection where possible.',
        'avoid_note': 'Avoid prolonged drought and poorly managed water stress.',
        'profile': {'season': 'wet', 'soil': 'loam', 'water': 'high', 'farm': 'rainfed', 'pref': 'resilient', 'bad_water': 'low'},
    },
    {
        'name': 'Mango',
        'category': Crop.Category.FRUIT,
        'description': 'Fruit tree preferring good drainage and dry flowering periods.',
        'planting_note': 'Encourage canopy airflow and avoid stagnant water around roots.',
        'avoid_note': 'Avoid waterlogged clay lowlands.',
        'profile': {'season': 'dry', 'soil': 'sandy', 'water': 'moderate', 'farm': 'rainfed', 'pref': 'resilient', 'bad_water': 'high'},
    },
    {
        'name': 'Pineapple',
        'category': Crop.Category.FRUIT,
        'description': 'Fruit crop favoring well-drained soils and moderate moisture.',
        'planting_note': 'Maintain drainage and clean field sanitation.',
        'avoid_note': 'Avoid heavy flooding and poorly drained clay.',
        'profile': {'season': 'dry', 'soil': 'sandy', 'water': 'moderate', 'farm': 'rainfed', 'pref': 'resilient', 'bad_water': 'high'},
    },
    {
        'name': 'Calamansi',
        'category': Crop.Category.FRUIT,
        'description': 'Citrus crop with moderate adaptability to Philippine conditions.',
        'planting_note': 'Support with regular pruning and nutrient management.',
        'avoid_note': 'Avoid prolonged waterlogging and severe drought.',
        'profile': {'season': 'dry', 'soil': 'loam', 'water': 'moderate', 'farm': 'rainfed', 'pref': 'resilient', 'bad_water': 'high'},
    },
    {
        'name': 'Avocado',
        'category': Crop.Category.FRUIT,
        'description': 'Perennial fruit tree suitable for well-drained and moderately moist sites.',
        'planting_note': 'Protect young trees from strong winds and standing water.',
        'avoid_note': 'Avoid lowland flooding conditions.',
        'profile': {'season': 'wet', 'soil': 'loam', 'water': 'moderate', 'farm': 'rainfed', 'pref': 'resilient', 'bad_water': 'high'},
    },
    {
        'name': 'Onion',
        'category': Crop.Category.VEGETABLE_SPICE,
        'description': 'High-value bulb crop favoring dry periods and good drainage.',
        'planting_note': 'Use raised beds and strict moisture control near harvest.',
        'avoid_note': 'Avoid heavy rainfall windows and high standing water.',
        'profile': {'season': 'dry', 'soil': 'sandy', 'water': 'low', 'farm': 'irrigated', 'pref': 'vegetable', 'bad_water': 'high'},
    },
    {
        'name': 'Garlic',
        'category': Crop.Category.VEGETABLE_SPICE,
        'description': 'Bulb spice crop suited to dry season and light soils.',
        'planting_note': 'Ensure proper spacing and avoid overwatering.',
        'avoid_note': 'Avoid high humidity and poorly drained fields.',
        'profile': {'season': 'dry', 'soil': 'sandy', 'water': 'low', 'farm': 'irrigated', 'pref': 'vegetable', 'bad_water': 'high'},
    },
    {
        'name': 'Tomato',
        'category': Crop.Category.VEGETABLE_SPICE,
        'description': 'Common vegetable crop requiring balanced moisture and loam soil.',
        'planting_note': 'Stake plants and monitor disease during humid weeks.',
        'avoid_note': 'Avoid constant heavy rains and waterlogging.',
        'profile': {'season': 'dry', 'soil': 'loam', 'water': 'moderate', 'farm': 'irrigated', 'pref': 'vegetable', 'bad_water': 'high'},
    },
    {
        'name': 'Eggplant',
        'category': Crop.Category.VEGETABLE_SPICE,
        'description': 'Resilient vegetable with good productivity in warm conditions.',
        'planting_note': 'Use proper spacing and prune old leaves for airflow.',
        'avoid_note': 'Avoid prolonged flooding and saturated soils.',
        'profile': {'season': 'dry', 'soil': 'loam', 'water': 'moderate', 'farm': 'rainfed', 'pref': 'vegetable', 'bad_water': 'high'},
    },
    {
        'name': 'Okra',
        'category': Crop.Category.VEGETABLE_SPICE,
        'description': 'Warm-season vegetable with moderate drought tolerance.',
        'planting_note': 'Harvest regularly to maintain pod quality.',
        'avoid_note': 'Avoid heavy flooding and prolonged cold-wet conditions.',
        'profile': {'season': 'dry', 'soil': 'sandy', 'water': 'moderate', 'farm': 'rainfed', 'pref': 'vegetable', 'bad_water': 'high'},
    },
    {
        'name': 'Ampalaya',
        'category': Crop.Category.VEGETABLE_SPICE,
        'description': 'Vining vegetable favoring warm weather and moderate watering.',
        'planting_note': 'Use trellis support and maintain regular but not excessive watering.',
        'avoid_note': 'Avoid persistent waterlogging and severe flooding.',
        'profile': {'season': 'dry', 'soil': 'loam', 'water': 'moderate', 'farm': 'rainfed', 'pref': 'vegetable', 'bad_water': 'high'},
    },
    {
        'name': 'String Beans',
        'category': Crop.Category.VEGETABLE_SPICE,
        'description': 'Leguminous vegetable suited to moderate moisture and good drainage.',
        'planting_note': 'Provide staking for climbing types and monitor pod borers.',
        'avoid_note': 'Avoid overly wet soil conditions.',
        'profile': {'season': 'dry', 'soil': 'loam', 'water': 'moderate', 'farm': 'rainfed', 'pref': 'vegetable', 'bad_water': 'high'},
    },
    {
        'name': 'Cabbage',
        'category': Crop.Category.VEGETABLE_SPICE,
        'description': 'Cooler-condition vegetable for managed or upland settings.',
        'planting_note': 'Perform best in cooler windows and controlled watering.',
        'avoid_note': 'Avoid hot-dry lowland stress periods.',
        'profile': {'season': 'wet', 'soil': 'loam', 'water': 'moderate', 'farm': 'irrigated', 'pref': 'vegetable', 'bad_water': 'low'},
    },
    {
        'name': 'Squash',
        'category': Crop.Category.VEGETABLE_SPICE,
        'description': 'Adaptable vegetable crop with broad field suitability.',
        'planting_note': 'Use proper spacing and pollination-friendly field management.',
        'avoid_note': 'Avoid severe water stress during fruit set.',
        'profile': {'season': 'dry', 'soil': 'silt', 'water': 'moderate', 'farm': 'rainfed', 'pref': 'vegetable', 'bad_water': 'low'},
    },
    {
        'name': 'Ginger',
        'category': Crop.Category.VEGETABLE_SPICE,
        'description': 'Spice crop favoring moist but well-drained conditions.',
        'planting_note': 'Use disease-free rhizomes and maintain mulch cover.',
        'avoid_note': 'Avoid long drought periods and compacted soils.',
        'profile': {'season': 'wet', 'soil': 'loam', 'water': 'moderate', 'farm': 'rainfed', 'pref': 'vegetable', 'bad_water': 'low'},
    },
    {
        'name': 'Lettuce',
        'category': Crop.Category.VEGETABLE_SPICE,
        'description': 'Leafy vegetable requiring mild conditions and careful irrigation.',
        'planting_note': 'Prefer cooler planting windows and frequent light watering.',
        'avoid_note': 'Avoid extreme heat and prolonged dry stress.',
        'profile': {'season': 'wet', 'soil': 'loam', 'water': 'moderate', 'farm': 'irrigated', 'pref': 'vegetable', 'bad_water': 'low'},
    },
    {
        'name': 'Pechay',
        'category': Crop.Category.VEGETABLE_SPICE,
        'description': 'Short-cycle leafy vegetable for quick harvest cycles.',
        'planting_note': 'Keep soil moisture consistent and harvest at marketable size.',
        'avoid_note': 'Avoid severe drought and unmanaged heat stress.',
        'profile': {'season': 'dry', 'soil': 'loam', 'water': 'moderate', 'farm': 'irrigated', 'pref': 'vegetable', 'bad_water': 'low'},
    },
]


class Command(BaseCommand):
    help = 'Seed initial crops and rules for AgriRulePH.'

    def handle(self, *args, **options):
        crop_lookup = {}
        created_crops = 0
        updated_crops = 0

        for item in CROPS:
            crop, created = Crop.objects.update_or_create(
                name=item['name'],
                defaults={
                    'category': item['category'],
                    'description': item['description'],
                    'planting_note': item['planting_note'],
                    'avoid_note': item['avoid_note'],
                    'is_active': True,
                },
            )
            crop_lookup[crop.name] = (crop, item['profile'])
            if created:
                created_crops += 1
            else:
                updated_crops += 1

        created_rules = 0
        updated_rules = 0

        def upsert_rule(name, crop, score, rule_type, explanation, **conditions):
            nonlocal created_rules, updated_rules
            defaults = {
                'crop': crop,
                'score': score,
                'rule_type': rule_type,
                'explanation': explanation,
                'is_active': True,
                'season_condition': conditions.get('season_condition', ''),
                'soil_type_condition': conditions.get('soil_type_condition', ''),
                'water_availability_condition': conditions.get('water_availability_condition', ''),
                'farm_type_condition': conditions.get('farm_type_condition', ''),
                'soil_ph_condition': conditions.get('soil_ph_condition', ''),
                'budget_level_condition': conditions.get('budget_level_condition', ''),
                'crop_preference_condition': conditions.get('crop_preference_condition', ''),
            }
            _, created = Rule.objects.update_or_create(name=name, defaults=defaults)
            if created:
                created_rules += 1
            else:
                updated_rules += 1

        avoid_on_low_water = {'Rice', 'Cacao', 'Abaca', 'Banana'}
        avoid_on_high_water = {'Onion', 'Garlic'}
        avoid_on_dry_season = {'Cabbage', 'Lettuce'}

        for crop_name, (crop, profile) in crop_lookup.items():
            safe = crop_name.lower().replace(' ', '_').replace('(', '').replace(')', '')

            # Remove legacy generated avoid rule names from earlier seed versions.
            Rule.objects.filter(name=f'R6_{safe}_critical_avoid').delete()
            Rule.objects.filter(name=f'R7_{safe}_critical_avoid').delete()
            Rule.objects.filter(name=f'R8_{safe}_critical_avoid').delete()

            upsert_rule(
                name=f'R1_{safe}_preferred_soil',
                crop=crop,
                score=15,
                rule_type=Rule.RuleType.POSITIVE,
                explanation=f'+15 points: {crop_name} prefers {profile["soil"]} soil.',
                soil_type_condition=profile['soil'],
            )
            upsert_rule(
                name=f'R2_{safe}_preferred_water',
                crop=crop,
                score=15,
                rule_type=Rule.RuleType.POSITIVE,
                explanation=f'+15 points: Water level suits {crop_name}.',
                water_availability_condition=profile['water'],
            )
            upsert_rule(
                name=f'R3_{safe}_season_preference',
                crop=crop,
                score=10,
                rule_type=Rule.RuleType.POSITIVE,
                explanation=f'+10 points: Current season supports {crop_name}.',
                season_condition=profile['season'],
            )
            upsert_rule(
                name=f'R4_{safe}_preference_support',
                crop=crop,
                score=8,
                rule_type=Rule.RuleType.POSITIVE,
                explanation=f'+8 points: Crop preference aligns with {crop_name}.',
                crop_preference_condition=profile['pref'],
            )

            upsert_rule(
                name=f'R5_{safe}_water_penalty',
                crop=crop,
                score=12,
                rule_type=Rule.RuleType.NEGATIVE,
                explanation=f'-12 points: Water condition is poor for {crop_name}.',
                water_availability_condition=profile['bad_water'],
            )

            if crop_name in avoid_on_low_water:
                upsert_rule(
                    name=f'R6_{safe}_critical_avoid_water',
                    crop=crop,
                    score=50,
                    rule_type=Rule.RuleType.AVOID,
                    explanation=f'Avoid: {crop_name} is strongly unsuitable when water availability is Low.',
                    water_availability_condition=ConsultationChoices.WaterAvailability.LOW,
                )
            else:
                Rule.objects.filter(name=f'R6_{safe}_critical_avoid_water').delete()

            if crop_name in avoid_on_high_water:
                upsert_rule(
                    name=f'R7_{safe}_critical_avoid_water',
                    crop=crop,
                    score=50,
                    rule_type=Rule.RuleType.AVOID,
                    explanation=f'Avoid: {crop_name} is strongly unsuitable when water availability is High.',
                    water_availability_condition=ConsultationChoices.WaterAvailability.HIGH,
                )
            else:
                Rule.objects.filter(name=f'R7_{safe}_critical_avoid_water').delete()

            if crop_name in avoid_on_dry_season:
                upsert_rule(
                    name=f'R8_{safe}_critical_avoid_season',
                    crop=crop,
                    score=50,
                    rule_type=Rule.RuleType.AVOID,
                    explanation=f'Avoid: {crop_name} is strongly unsuitable during Dry season conditions.',
                    season_condition=ConsultationChoices.Season.DRY,
                )
            else:
                Rule.objects.filter(name=f'R8_{safe}_critical_avoid_season').delete()

        total_rules = Rule.objects.count()

        self.stdout.write(self.style.SUCCESS(f'Crops created: {created_crops}, updated: {updated_crops}'))
        self.stdout.write(self.style.SUCCESS(f'Rules created: {created_rules}, updated: {updated_rules}, total now: {total_rules}'))
