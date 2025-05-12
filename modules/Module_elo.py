"""Module pour stocker les fonctions utiles à la partie ELO"""


def search_player(df, first_name=None, last_name=None):
    """Fonction qui permet de chercher un joueur dans un DataFrame à partir de son nom et ou prénom et de 
    récupérer plusieurs infos à son sujet dont son ID.
    
    La fonction prend en entrée ;
        df : le dataframe
        first_name = Prénom
        last_name = Nom de famille
        
        
    On peut ne remplir qu'un seul des arguments d'identité, cela cherche alors tous les joueurs avec ce nom de famille ou prénom
    
    
    """

    query = []
    if first_name:
        query.append(f"FirstName == '{first_name}'")
    if last_name:
        query.append(f"LastName == '{last_name}'")
    query_str = " & ".join(query)
    
    if query_str:
        results = df.query(query_str)
        if not results.empty:
            display(results)
        else:
            print("Aucun joueur trouvé avec ces critères. Essayez avec une majuscule unique au début")
    else:
        print("Veuillez fournir au moins un prénom ou un nom.")
        
        
        
        
        
        
def plot_elo_comparison(player_ids, df_matches_singles, df_male_players):
    """
    Fonction pour tracer la comparaison de la progression des points ELO de plusieurs joueurs.

    La fonction prend en entrée :
        player_ids : Liste des IDs des joueurs à comparer.
        df_matches_singles : DataFrame contenant les matchs en simple.
        df_male_players : DataFrame contenant les informations des joueurs.
    """
    
    import matplotlib.pyplot as plt
    
    # Initialiser la figure pour le graphique
    plt.figure(figsize=(20, 6))

    for player_id in player_ids:
        # Convertir player_id en str
        player_id = str(player_id)

        # Filtrer les matchs du joueur
        player_matches = df_matches_singles[
            (df_matches_singles["Player1Id"] == player_id) | 
            (df_matches_singles["Player2Id"] == player_id)
        ]

        if player_matches.empty:
            print(f"Aucun match trouvé pour le joueur avec l'ID {player_id}.")
            continue

        # Extraire les points ELO après chaque match
        elo_after = player_matches.apply(
            lambda row: row["Player1EloAfter"] if row["Player1Id"] == player_id else row["Player2EloAfter"], axis=1
        )

        # Récupérer le nom du joueur
        player_info = df_male_players[df_male_players["PlayerId"] == player_id]
        if player_info.empty:
            print(f"Aucun joueur trouvé avec l'ID {player_id}.")
            continue

        player_name = player_info["FirstName"].values[0] + " " + player_info["LastName"].values[0]

        # Ajouter la courbe au graphe
        dates = player_matches["Date"]
        plt.plot(dates, elo_after, label=f"{player_name} (ID: {player_id})")

    # Configurer les labels et le titre du graphique
    plt.xlabel("Date")
    plt.ylabel("Points ELO")
    plt.title("Comparaison de la progression des points ELO")
    plt.legend()
    plt.grid(True)
    plt.show()