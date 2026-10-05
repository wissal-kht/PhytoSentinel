model_mapping_dict = {
    'Apple': {
        'classes': ['Apple Scab', 'Black Rot', 'Cedar Apple Rust', 'Healthy'],
        'model_path': 'apple_model.h5'
    },
    'Cherry': {
        'classes': ['Healthy', 'Powdery Mildew'],
        'model_path': 'cherry_model.h5'
    },
    'Corn': {
        'classes': ['Common Rust', 'Gray Leaf Spot', 'Healthy', 'Northern Leaf Blight'],
        'model_path': 'corn_model.h5'
    },
    'Grape': {
        'classes': ['Black Rot', 'Esca', 'Healthy', 'Leaf Blight'],
        'model_path': 'grape_model.h5'
    },
    'Peach': {
        'classes': ['Bacterial Spot', 'Healthy'],
        'model_path': 'peach_model.h5'
    },
    'Pepper': {
        'classes': ['Bacterial Spot', 'Healthy'],
        'model_path': 'pepper_model.h5'
    },
    'Potato': {
        'classes': ['Early Blight', 'Healthy', 'Late Blight'],
        'model_path': 'potato_model.h5'
    },
    'Strawberry': {
        'classes': ['Healthy', 'Leaf Scorch'],
        'model_path': 'strawberry_model.h5'
    },
    'Tomato': {
        'classes': ['Bacterial Spot', 'Early Blight', 'Healthy', 'Late Blight'],
        'model_path': 'tomato_model.h5'
    }
}

plant_disease_dict = {
    'Healthy': {
        'Description': '*A healthy plant exhibits vigorous growth and has no visible signs of disease or pest infestation. The leaves are typically green and free from discoloration, spots, or lesions. The stems are firm and erect, and the overall plant appearance is robust.*',
        'Symptoms': '*No symptoms; plant appears normal and free from any abnormalities.*',
        'Treatment': '*No treatment is required for a healthy plant. However, proper cultural practices such as adequate watering, fertilization, and pest management can help maintain plant health.*',
        'scientific_name': None,
        'severity': 'low',
        'severity_indicators': {'infection': 0, 'vitesse': 0, 'risque': 0},
        'treatment_steps': [],
        'is_healthy': True
    },
    'Apple': {
        'Apple Scab': {
            'Description': '*Apple scab is a fungal disease that causes dark, scabby marks on the leaves and fruit of apple and crabapple trees. It is caused by the fungus Venturia inaequalis, which spreads by airborne spores and survives the winter on fallen leaves.*',
            'Symptoms': '*Small, brown or olive-green spots on the underside of young leaves, or on either side of older leaves.*',
            'Treatment': '*To control apple scab, practice good sanitation by removing fallen leaves and fruit from the ground. Apply fungicides as directed.*',
            'scientific_name': 'Venturia inaequalis',
            'severity': 'moderate',
            'severity_indicators': {'infection': 60, 'vitesse': 55, 'risque': 50},
            'treatment_steps': [
                'Appliquer un fongicide à base de captane ou de myclobutanil dès l\'apparition des symptômes.',
                'Ramasser et détruire les feuilles tombées pour éliminer les spores hivernantes.',
                'Tailler les branches pour améliorer la circulation de l\'air.',
                'Effectuer des traitements préventifs au débourrement au printemps.'
            ],
            'is_healthy': False
        },
        'Black Rot': {
            'Description': '*Black rot is a disease caused by the fungus Botryosphaeria obtusa that affects apple trees. It can cause reduced fruit productivity and quality, and can weaken the tree.*',
            'Symptoms': '*Small purple spots that develop into brownish-tan centers with darker margins and a purple outline, giving the leaves a "frog-eye" appearance.*',
            'Treatment': '*To control black rot, prune infected branches and remove and destroy infected fruit. Apply fungicides during the growing season.*',
            'scientific_name': 'Botryosphaeria obtusa',
            'severity': 'critical',
            'severity_indicators': {'infection': 75, 'vitesse': 65, 'risque': 70},
            'treatment_steps': [
                'Éliminer immédiatement les branches atteintes de chancres par taille sévère.',
                'Appliquer un fongicide à base de thiophanate-méthyle ou de captan.',
                'Désinfecter les outils de taille avec une solution d\'alcool à 70%.',
                'Retirer les fruits momifiés qui restent sur l\'arbre.',
                'Améliorer le drainage du sol pour éviter l\'excès d\'humidité.'
            ],
            'is_healthy': False
        },
        'Cedar Apple Rust': {
            'Description': '*Cedar apple rust is a fungal disease that affects apple and cedar trees. It is caused by the fungus Gymnosporangium juniperi-virginianae, which requires both apple and cedar trees to complete its life cycle. The disease appears as orange or yellow spots on the leaves and fruit of apple trees.*',
            'Symptoms': '*Orange or yellow spots on the leaves and fruit. The spots may enlarge and develop a reddish-brown color. Spore-producing structures called telia may also form on the underside of the leaves.*',
            'Treatment': '*To control cedar apple rust, remove and destroy infected plant material. Prune nearby cedar trees to reduce spore production. Apply fungicides as directed.*',
            'scientific_name': 'Gymnosporangium juniperi-virginianae',
            'severity': 'moderate',
            'severity_indicators': {'infection': 45, 'vitesse': 40, 'risque': 50},
            'treatment_steps': [
                'Appliquer un fongicide à base de myclobutanil ou de propiconazole au printemps.',
                'Supprimer les genévriers proches qui servent d\'hôtes secondaires si possible.',
                'Traiter de façon préventive dès le gonflement des bourgeons.',
                'Choisir des variétés résistantes lors du renouvellement du verger.'
            ],
            'is_healthy': False
        }
    },
    'Cherry': {
        'Powdery Mildew': {
            'Description': '*Powdery mildew is a fungal disease that affects cherry trees. It appears as white, powdery spots on the leaves and shoots. The disease is caused by various species of fungi from the Erysiphaceae family, which thrive in humid conditions.*',
            'Symptoms': '*White, powdery spots on the upper surfaces of leaves, shoots, and sometimes fruit. Infected leaves may become distorted or yellowed. Severe infections can cause premature leaf drop and reduced fruit quality.*',
            'Treatment': '*To control powdery mildew, remove and destroy infected plant material. Apply fungicides labeled for powdery mildew control, following label instructions carefully. Improve air circulation around plants by pruning and spacing trees appropriately.*',
            'scientific_name': 'Podosphaera clandestina',
            'severity': 'moderate',
            'severity_indicators': {'infection': 55, 'vitesse': 50, 'risque': 45},
            'treatment_steps': [
                'Appliquer du soufre mouillable ou un fongicide systémique à base de tébuconazole.',
                'Éviter les excès d\'azote qui favorisent une végétation tendre susceptible.',
                'Améliorer la circulation de l\'air par une taille appropriée.',
                'Irriguer au sol et éviter de mouiller le feuillage.'
            ],
            'is_healthy': False
        }

    },
    'Corn': {
        'Common Rust': {
            'Description': '*Common rust is a fungal disease caused by the pathogen Puccinia sorghi that affects corn plants. It appears as small, reddish-brown pustules on the leaves, stems, and husks of corn plants. The disease is favored by warm temperatures and high humidity.*',
            'Symptoms': '*Small, reddish-brown pustules on the upper surfaces of corn leaves. As the disease progresses, the pustules may coalesce, leading to widespread discoloration and weakening of the affected plant tissues.*',
            'Treatment': '*To control common rust, apply fungicides as directed. Plant resistant corn varieties to reduce the risk of infection.*',
            'scientific_name': 'Puccinia sorghi',
            'severity': 'moderate',
            'severity_indicators': {'infection': 50, 'vitesse': 60, 'risque': 55},
            'treatment_steps': [
                'Appliquer un fongicide à base de triazole (propiconazole, tébuconazole) dès les premiers symptômes.',
                'Utiliser des hybrides résistants dans les zones à risque élevé.',
                'Surveiller les parcelles régulièrement en période à risque (temps frais et humide).'
            ],
            'is_healthy': False
        },
        'Gray Leaf Spot': {
            'Description': '*Gray leaf spot is a fungal disease caused by the pathogen Cercospora zeae-maydis that affects corn plants. It appears as rectangular, grayish lesions on the leaves, limited by the leaf veins. The disease can significantly reduce yield in severe cases.*',
            'Symptoms': '*Rectangular, gray or tan lesions on the leaves, delimited by the leaf veins. Lesions may coalesce and cover large portions of the leaf surface, leading to widespread discoloration and weakening of the plant.*',
            'Treatment': '*To control gray leaf spot, apply fungicides as directed. Practice crop rotation to reduce the risk of infection.*',
            'scientific_name': 'Cercospora zeae-maydis',
            'severity': 'moderate',
            'severity_indicators': {'infection': 60, 'vitesse': 55, 'risque': 65},
            'treatment_steps': [
                'Appliquer un fongicide à base de strobilurine (azoxystrobine) ou de triazole.',
                'Pratiquer la rotation des cultures — éviter le maïs après maïs.',
                'Labourer les résidus de récolte pour réduire l\'inoculum.',
                'Choisir des hybrides résistants à la tache grise.'
            ],
            'is_healthy': False
        },
        'Northern Leaf Blight': {
            'Description': '*Northern leaf blight is a fungal disease caused by the pathogen Exserohilum turcicum that affects corn plants. It appears as long, elliptical, grayish-green to tan lesions on the leaves. The disease can cause yield losses of up to 50% in favorable conditions.*',
            'Symptoms': '*Long, elliptical, grayish-green to tan lesions on the leaves. Lesions may enlarge and coalesce, leading to widespread blighting of the foliage. Infected plants may also exhibit reduced ear development and poor kernel fill.*',
            'Treatment': '*To control northern leaf blight, apply fungicides as directed. Plant resistant corn varieties to reduce the risk of infection.*',
            'scientific_name': 'Exserohilum turcicum',
            'severity': 'critical',
            'severity_indicators': {'infection': 70, 'vitesse': 60, 'risque': 70},
            'treatment_steps': [
                'Appliquer un fongicide systémique (azoxystrobine + propiconazole) dès l\'apparition des premières lésions.',
                'Privilégier des hybrides résistants ou tolérants.',
                'Effectuer une rotation avec des cultures non-hôtes (blé, soja, tournesol).',
                'Incorporer les résidus de culture infectés dans le sol après la récolte.'
            ],
            'is_healthy': False
        }
    },
    'Grape': {
        'Black Rot': {
            'Description': '*Black rot is a fungal disease caused by the pathogen Guignardia bidwellii that affects grapevines. It appears as brown, necrotic lesions on the leaves, shoots, and fruit. The disease can cause significant yield losses if left uncontrolled.*',
            'Symptoms': '*Black, necrotic lesions on the leaves, shoots, and fruit. Lesions may expand and coalesce, leading to widespread blighting of the affected plant parts. Infected fruit may shrivel and become mummified.*',
            'Treatment': '*To control black rot, remove and destroy infected plant material. Practice good vineyard management, including proper pruning, spacing, and trellising to improve air circulation. Apply fungicides preventatively, especially during periods of warm, humid weather and susceptible growth stages.*',
            'scientific_name': 'Guignardia bidwellii',
            'severity': 'critical',
            'severity_indicators': {'infection': 80, 'vitesse': 70, 'risque': 80},
            'treatment_steps': [
                'Appliquer du mancozèbe ou du myclobutanil de façon préventive dès le débourrement.',
                'Retirer et détruire (brûler) les grappes et feuilles atteintes.',
                'Éliminer les sarments et grappes momifiées lors de la taille hivernale.',
                'Assurer une bonne aération du feuillage par effeuillage et palissage.',
                'Traiter toutes les 7-10 jours en période pluvieuse.'
            ],
            'is_healthy': False
        },

        'Esca': {
            'Description': '*Esca is a complex of fungal diseases affecting grapevines. It includes several different disorders, such as young vine decline, esca proper, and grapevine leaf stripe disease. These diseases cause various symptoms, including leaf discoloration, shoot dieback, and internal wood necrosis.*',
            'Symptoms': '*Symptoms of esca can vary depending on the specific disorder within the complex. Common symptoms include yellow or reddish-brown discoloration of leaves, internal wood necrosis in the trunk and cordons, and shoot dieback. The characteristic "tiger-striped" pattern may also appear on leaves.*',
            'Treatment': '*Management of esca is challenging due to its complexity and variability. Cultural practices such as pruning, canopy management, and irrigation can help reduce disease pressure. Application of fungicides may provide some control, but their efficacy can be limited.*',
            'scientific_name': 'Phaeomoniella chlamydospora / Phaeoacremonium spp.',
            'severity': 'critical',
            'severity_indicators': {'infection': 75, 'vitesse': 40, 'risque': 80},
            'treatment_steps': [
                'Aucun traitement curatif efficace n\'est disponible à ce jour.',
                'Pratiquer la chirurgie du bois (curetage) sur les ceps présentant des nécroses.',
                'Protéger les plaies de taille avec une pâte fongicide (Trichoderma).',
                'Éviter les grandes plaies de taille — étaler la taille sur plusieurs années.',
                'Arracher et remplacer les ceps fortement atteints.'
            ],
            'is_healthy': False
        },


        'Leaf Blight': {
            'Description': '*Leaf blight is a fungal disease caused by various pathogens that affect grapevines. It appears as brown, necrotic lesions on the leaves, often surrounded by a yellow halo. The disease can lead to defoliation and reduced fruit quality if left uncontrolled.*',
            'Symptoms': '*Brown, necrotic lesions on the leaves, often with a yellow halo around the edges. Lesions may coalesce and cover large portions of the leaf surface. Severe infections can cause defoliation and weaken the vine.*',
            'Treatment': '*To control leaf blight, remove and destroy infected plant material. Practice good vineyard management, including proper pruning, spacing, and trellising to improve air circulation. Apply fungicides preventatively, especially during periods of warm, humid weather and susceptible growth stages.*',
            'scientific_name': 'Pseudocercospora vitis',
            'severity': 'moderate',
            'severity_indicators': {'infection': 55, 'vitesse': 45, 'risque': 50},
            'treatment_steps': [
                'Appliquer un fongicide à base de mancozèbe ou de cuivre dès les premiers symptômes.',
                'Assurer une bonne aération du feuillage par effeuillage et palissage.',
                'Éliminer et détruire les feuilles tombées pour réduire l\'inoculum.',
                'Pratiquer la rotation des traitements pour éviter les résistances.'
            ],
            'is_healthy': False
        }


    },
    'Peach': {
        'Bacterial Spot': {
            'Description': '*Bacterial spot is a common bacterial disease affecting peach trees. It is caused by the bacterium Xanthomonas arboricola pv. pruni and can cause significant damage to leaves, fruit, and shoots. The disease is favored by warm, humid conditions and can spread rapidly during wet weather.*',
            'Symptoms': '*Symptoms of bacterial spot include small, water-soaked lesions on the leaves, which later turn brown and may have a yellow halo. Lesions on the fruit may appear as small, raised spots with a water-soaked appearance. Severe infections can cause defoliation and fruit loss.*',
            'Treatment': '*To control bacterial spot, practice good sanitation by removing and destroying infected plant material. Apply copper-based fungicides or bactericides as directed, especially during periods of high disease pressure. Prune trees to improve air circulation and reduce disease spread.*',
            'scientific_name': 'Xanthomonas arboricola pv. pruni',
            'severity': 'moderate',
            'severity_indicators': {'infection': 65, 'vitesse': 55, 'risque': 60},
            'treatment_steps': [
                'Appliquer des traitements cupriques (oxychlorure de cuivre) en préventif dès le débourrement.',
                'Éviter les blessures mécaniques qui facilitent la pénétration bactérienne.',
                'Tailler les rameaux atteints et désinfecter les outils après chaque coupe.',
                'Choisir des variétés moins sensibles lors du renouvellement du verger.',
                'Éviter les excès d\'irrigation par aspersion.'
            ],
            'is_healthy': False
        }

    },
    'Pepper': {
        'Bacterial Spot': {
            'Description': '*Bacterial spot is a common bacterial disease affecting pepper plants. It is caused by the bacterium Xanthomonas campestris pv. vesicatoria and can cause significant damage to leaves, fruit, and stems. The disease is favored by warm, humid conditions and can spread rapidly during wet weather.*',
            'Symptoms': '*Symptoms of bacterial spot include small, water-soaked lesions on the leaves, which later turn brown and may have a yellow halo. Lesions on the fruit may appear as small, raised spots with a water-soaked appearance. Severe infections can cause defoliation and fruit loss.*',
            'Treatment': '*To control bacterial spot, practice good sanitation by removing and destroying infected plant material. Apply copper-based fungicides or bactericides as directed, especially during periods of high disease pressure. Prune plants to improve air circulation and reduce disease spread.*',
            'scientific_name': 'Xanthomonas campestris pv. vesicatoria',
            'severity': 'moderate',
            'severity_indicators': {'infection': 60, 'vitesse': 55, 'risque': 60},
            'treatment_steps': [
                'Appliquer de l\'oxychlorure de cuivre ou de la bouillie bordelaise en préventif.',
                'Utiliser des semences saines et certifiées, ou les désinfecter avant le semis.',
                'Pratiquer la rotation des cultures (éviter solanacées pendant 2-3 ans).',
                'Éviter l\'irrigation par aspersion et travailler dans les cultures lorsque le feuillage est sec.',
                'Éliminer les résidus de plantes infectées après la récolte.'
            ],
            'is_healthy': False
        },

    },
    'Potato': {
        'Early Blight': {
            'Description': '*Early blight is a fungal disease caused by the pathogen Alternaria solani that affects potato plants. It appears as dark, concentric rings with yellow halos on the leaves, starting from the lower leaves and progressing upward. The disease is favored by warm, humid conditions and can spread rapidly in dense plantings.*',
            'Symptoms': '*Dark, concentric rings with yellow halos on the leaves, starting from the lower leaves and progressing upward. Lesions may enlarge and coalesce, leading to widespread blighting of the foliage. Infected tubers may develop sunken, dark lesions with concentric rings on the skin.*',
            'Treatment': '*To control early blight, practice good sanitation by removing and destroying infected plant material. Apply fungicides as directed, especially during periods of high disease pressure. Proper crop rotation and planting disease-resistant varieties can also help reduce disease incidence.*',
            'scientific_name': 'Alternaria solani',
            'severity': 'moderate',
            'severity_indicators': {'infection': 55, 'vitesse': 50, 'risque': 55},
            'treatment_steps': [
                'Appliquer un fongicide à base de mancozèbe ou de chlorothalonil dès les premiers symptômes.',
                'Assurer une fertilisation équilibrée, notamment en azote et en potassium.',
                'Pratiquer la rotation des cultures sur 2-3 ans.',
                'Éliminer les feuilles basses atteintes et les débris végétaux après récolte.'
            ],
            'is_healthy': False
        },
        'Late Blight': {
            'Description': '*Late blight is a devastating fungal disease caused by the pathogen Phytophthora infestans that affects potato plants. It appears as dark, water-soaked lesions on the leaves, stems, and tubers, often accompanied by a white, fuzzy growth on the undersides of the leaves. The disease thrives in cool, wet conditions and can spread rapidly during periods of high humidity.*',
            'Symptoms': '*Dark, water-soaked lesions on the leaves, stems, and tubers, often with a white, fuzzy growth on the undersides of the leaves. Lesions may rapidly expand and coalesce, leading to widespread blighting of the foliage and rotting of the tubers. Infected tubers may develop a foul odor and become soft and watery.*',
            'Treatment': '*To control late blight, practice good sanitation by removing and destroying infected plant material. Apply fungicides as directed, especially during periods of high disease pressure. Proper crop rotation, planting disease-resistant varieties, and avoiding overhead irrigation can also help reduce disease incidence.*',
            'scientific_name': 'Phytophthora infestans',
            'severity': 'critical',
            'severity_indicators': {'infection': 88, 'vitesse': 92, 'risque': 90},
            'treatment_steps': [
                'Traitement d\'urgence avec métalaxyl + mancozèbe — répéter tous les 7 jours en conditions favorables.',
                'Buttage des rangs pour protéger les tubercules contre les spores lessivées.',
                'Éliminer et détruire les fanes atteintes avant la récolte.',
                'Utiliser des variétés résistantes et des plants certifiés sains.',
                'Surveiller les parcelles voisines de tomates qui partagent le même pathogène.'
            ],
            'is_healthy': False
        }

    },
    'Strawberry': {
        'Leaf Scorch': {
            'Description': '*Leaf scorch is a fungal disease that affects strawberry plants. It appears as brown, necrotic spots on the leaves, which may enlarge and coalesce over time. The disease is caused by various pathogens and can be exacerbated by environmental stressors such as drought or high temperatures.*',
            'Symptoms': '*Brown, necrotic spots on the leaves, often with irregular margins. Lesions may start as small spots and enlarge to cover large portions of the leaf surface. Severe infections can cause defoliation and weaken the plant.*',
            'Treatment': '*To control leaf scorch, remove and destroy infected plant material. Practice good sanitation by removing fallen leaves and debris from around the plants. Avoid overhead irrigation and water the plants at the base to reduce leaf wetness. Apply fungicides as directed, especially during periods of high disease pressure.*',
            'scientific_name': 'Diplocarpon earlianum',
            'severity': 'moderate',
            'severity_indicators': {'infection': 55, 'vitesse': 50, 'risque': 50},
            'treatment_steps': [
                'Appliquer un fongicide à base de myclobutanil ou de tébuconazole dès l\'apparition des symptômes.',
                'Supprimer et détruire les feuilles atteintes pour réduire l\'inoculum.',
                'Éviter l\'excès d\'humidité en irrigant au goutte-à-goutte plutôt que par aspersion.',
                'Renouveler les plantations tous les 2-3 ans avec des plants certifiés sains.'
            ],
            'is_healthy': False
        },

    },
    'Tomato': {
        'Bacterial Spot': {
            'Description': '*Bacterial spot is a common bacterial disease affecting tomato plants. It is caused by the bacterium Xanthomonas campestris pv. vesicatoria and can cause significant damage to leaves, fruit, and stems. The disease is favored by warm, humid conditions and can spread rapidly during wet weather.*',
            'Symptoms': '*Symptoms of bacterial spot include small, water-soaked lesions on the leaves, which later turn brown and may have a yellow halo. Lesions on the fruit may appear as small, raised spots with a water-soaked appearance. Severe infections can cause defoliation and fruit loss.*',
            'Treatment': '*To control bacterial spot, practice good sanitation by removing and destroying infected plant material. Apply copper-based fungicides or bactericides as directed, especially during periods of high disease pressure. Prune plants to improve air circulation and reduce disease spread.*',
            'scientific_name': 'Xanthomonas campestris pv. vesicatoria',
            'severity': 'moderate',
            'severity_indicators': {'infection': 60, 'vitesse': 55, 'risque': 60},
            'treatment_steps': [
                'Appliquer de l\'oxychlorure de cuivre en préventif et curatif.',
                'Utiliser des semences saines et traitées.',
                'Pratiquer la rotation des cultures.',
                'Éliminer les résidus de plantes infectées après la récolte.'
            ],
            'is_healthy': False
        },
        'Early Blight': {
            'Description': '*Early blight is a fungal disease caused by the pathogen Alternaria solani that affects tomato plants. It appears as dark, concentric rings with yellow halos on the leaves, starting from the lower leaves and progressing upward. The disease is favored by warm, humid conditions and can spread rapidly in dense plantings.*',
            'Symptoms': '*Dark, concentric rings with yellow halos on the leaves, starting from the lower leaves and progressing upward. Lesions may enlarge and coalesce, leading to widespread blighting of the foliage. Infected fruit may also develop sunken lesions with concentric rings on the skin.*',
            'Treatment': '*To control early blight, practice good sanitation by removing and destroying infected plant material. Apply fungicides as directed, especially during periods of high disease pressure. Proper crop rotation and planting disease-resistant varieties can also help reduce disease incidence.*',
            'scientific_name': 'Alternaria solani',
            'severity': 'moderate',
            'severity_indicators': {'infection': 60, 'vitesse': 50, 'risque': 55},
            'treatment_steps': [
                'Appliquer du mancozèbe ou du chlorothalonil dès les premiers symptômes.',
                'Éviter les déficits en azote et en potassium qui fragilisent les plants.',
                'Pratiquer la rotation des cultures sur 2-3 ans.',
                'Éliminer les feuilles basses atteintes en premier.'
            ],
            'is_healthy': False
        },
        'Late Blight': {
            'Description': '*Late blight is a devastating fungal disease caused by the pathogen Phytophthora infestans that affects tomato plants. It appears as dark, water-soaked lesions on the leaves, stems, and fruit, often accompanied by a white, fuzzy growth on the undersides of the leaves. The disease thrives in cool, wet conditions and can spread rapidly during periods of high humidity.*',
            'Symptoms': '*Dark, water-soaked lesions on the leaves, stems, and fruit, often with a white, fuzzy growth on the undersides of the leaves. Lesions may rapidly expand and coalesce, leading to widespread blighting of the foliage and rotting of the fruit. Infected fruit may develop a foul odor and become soft and watery.*',
            'Treatment': '*To control late blight, practice good sanitation by removing and destroying infected plant material. Apply fungicides as directed, especially during periods of high disease pressure. Proper crop rotation, planting disease-resistant varieties, and avoiding overhead irrigation can also help reduce disease incidence.*',
            'scientific_name': 'Phytophthora infestans',
            'severity': 'critical',
            'severity_indicators': {'infection': 88, 'vitesse': 92, 'risque': 88},
            'treatment_steps': [
                'Traitement d\'urgence avec métalaxyl + mancozèbe (2 kg/ha) — répéter tous les 7 jours.',
                'Améliorer la ventilation inter-rangs et réduire l\'humidité foliaire.',
                'Éliminer et brûler les plants très atteints.',
                'Surveiller les parcelles voisines de pommes de terre partageant le même pathogène.'
            ],
            'is_healthy': False
        }

    }
}