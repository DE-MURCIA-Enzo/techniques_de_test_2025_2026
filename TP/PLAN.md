# Plan pour les tests

## Idée générale
Je vais structurer les tests en trois niveaux pour couvrir la logique interne (unitaires), les interactions avec PointSetManager (intégration) et le comportement de l'API vu par un client (système). L’objectif est de détecter rapidement les erreurs de logique, de garantir une intégration robuste avec PointSetManager, et d’assurer que l’API se comporte correctement. Enfin, je ferai des tests de performance pour évaluer le temps de traitement sur des cas plus lourds.

## Différents tests

### Tests unitaires
L’objectif de ces tests est de vérifier la logique interne du triangulateur. Ils doivent confirmer que les fonctions de calcul produisent des résultats corrects sur des cas normaux et qu’elles renvoient des erreurs claires sur des entrées non valides.

### Tests d’intégration
L’objectif de ces tests est de vérifier le comportement du service face aux réponses du service externe. Je devrais donc mocker le PointSetManager pour simuler des réponses cohérentes, des erreurs et des contenus incohérents, afin de confirmer que le triangulateur réagit correctement sans planter et en levant des erreurs.

### Tests système
L’objectif de ces tests est de valider le service en l’utilisant exactement comme le ferait un client, en appelant directement l’API. Ils doivent confirmer que les réponses et les codes de statut sont corrects, et que des erreurs sont bien renvoyées.

### Performance
Enfin, je ferai des tests de performance dont l’objectif est de mesurer le temps de traitement sur des jeux de données plus volumineux. Le but est d’évaluer la tenue en charge (tests d’endurance) et de s’assurer que les exécutions ne sont pas trop longues.