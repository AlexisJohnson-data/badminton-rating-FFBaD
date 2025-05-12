# -*- coding: utf-8 -*-
"""
Ce module SmartRank présente la création d'un système original de rating pour le badminton.
Il s'inspire du système Glicko2, avec des spécificités propres au badminton,
et des paramètres supplémentaires.
"""

import math

WIN = 1.
LOSS = 0.

MU = 1800
PHI = 350
SIGMA = 0.06
TAU = 1.0
EPSILON = 0.000001

class Rating(object):
    def __init__(self, mu=MU, phi=PHI, sigma=SIGMA):
        self.mu = mu
        self.phi = phi
        self.sigma = sigma
        

    def __repr__(self):
        c = type(self)
        args = (c.__module__, c.__name__, self.mu, self.phi, self.sigma)
        return '%s.%s(mu=%.3f, phi=%.3f, sigma=%.3f)' % args


class SmartRank(object):
    def __init__(self, mu=MU, phi=PHI, sigma=SIGMA, tau=TAU, epsilon=EPSILON):
        self.mu = mu
        self.phi = phi
        self.sigma = sigma
        self.tau = tau
        self.epsilon = epsilon
        self.player_ratings = {}

    def create_rating(self, mu=None, phi=None, sigma=None, match_count=None):
        if mu is None:
            mu = self.mu
            
        if sigma is None:
            sigma = self.sigma
    
        # Déterminer PHI en fonction de l'activité
        if phi is None:
            if match_count is None:
                # Valeur par défaut si aucune donnée n'est disponible
                phi = self.phi
            elif match_count < 5:
                phi = 350  # Peu de matchs -> PHI élevé
            elif match_count <= 20:
                phi = 250  # Activité moyenne
            else:
                phi = 150  # Joueur très actif

        return Rating(mu, phi, sigma)

    def scale_down(self, rating, ratio=173.7178):
        mu = (rating.mu - self.mu) / ratio
        phi = rating.phi / ratio
        return self.create_rating(mu, phi, rating.sigma)

    def scale_up(self, rating, ratio=173.7178):
        mu = rating.mu * ratio + self.mu
        phi = rating.phi * ratio
        return self.create_rating(mu, phi, rating.sigma)

    def reduce_impact(self, rating):
        """The original form is `g(RD)`. This function reduces the impact of
        games as a function of an opponent's RD.
        """
        return 1. / math.sqrt(1 + (3 * rating.phi ** 2) / (math.pi ** 2))

    def expect_score(self, rating, other_rating, impact):
        return 1. / (1 + math.exp(-impact * (rating.mu - other_rating.mu)))

    def determine_sigma(self, rating, difference, variance):
        """Determines new sigma."""
        phi = rating.phi
        difference_squared = difference ** 2
        # 1. Let a = ln(s^2), and define f(x)
        alpha = math.log(rating.sigma ** 2)

        def f(x):
            """This function is twice the conditional log-posterior density of
            phi, and is the optimality criterion.
            """
            tmp = phi ** 2 + variance + math.exp(x)
            a = math.exp(x) * (difference_squared - tmp) / (2 * tmp ** 2)
            b = (x - alpha) / (self.tau ** 2)
            return a - b

        # 2. Set the initial values of the iterative algorithm.
        a = alpha
        if difference_squared > phi ** 2 + variance:
            b = math.log(difference_squared - phi ** 2 - variance)
        else:
            k = 1
            while f(alpha - k * math.sqrt(self.tau ** 2)) < 0:
                k += 1
            b = alpha - k * math.sqrt(self.tau ** 2)
        # 3. Let fA = f(A) and f(B) = f(B)
        f_a, f_b = f(a), f(b)
        # 4. While |B-A| > e, carry out the following steps.
        # (a) Let C = A + (A - B)fA / (fB-fA), and let fC = f(C).
        # (b) If fCfB < 0, then set A <- B and fA <- fB; otherwise, just set
        #     fA <- fA/2.
        # (c) Set B <- C and fB <- fC.
        # (d) Stop if |B-A| <= e. Repeat the above three steps otherwise.
        while abs(b - a) > self.epsilon:
            c = a + (a - b) * f_a / (f_b - f_a)
            f_c = f(c)
            if f_c * f_b < 0:
                a, f_a = b, f_b
            else:
                f_a /= 2
            b, f_b = c, f_c
        # 5. Once |B-A| <= e, set s' <- e^(A/2)
        return math.exp(1) ** (a / 2)

    def rate(self, rating, series):
        # Step 2. For each player, convert the rating and RD's onto the
        #         Glicko-2 scale.
        rating = self.scale_down(rating)
        # Step 3. Compute the quantity v. This is the estimated variance of the
        #         team's/player's rating based only on game outcomes.
        # Step 4. Compute the quantity difference, the estimated improvement in
        #         rating by comparing the pre-period rating to the performance
        #         rating based only on game outcomes.
        variance_inv = 0
        difference = 0
        if not series:
            # If the team didn't play in the series, do only Step 6
            phi_star = math.sqrt(rating.phi ** 2 + rating.sigma ** 2)
            return self.scale_up(self.create_rating(rating.mu, phi_star, rating.sigma))
        for actual_score, other_rating in series:
            other_rating = self.scale_down(other_rating)
            impact = self.reduce_impact(other_rating)
            expected_score = self.expect_score(rating, other_rating, impact)
            variance_inv += impact ** 2 * expected_score * (1 - expected_score)
            difference += impact * (actual_score - expected_score)
        difference /= variance_inv
        variance = 1. / variance_inv
        # Step 5. Determine the new value, Sigma', ot the sigma. This
        #         computation requires iteration.
        sigma = self.determine_sigma(rating, difference, variance)
        # Step 6. Update the rating deviation to the new pre-rating period
        #         value, Phi*.
        phi_star = math.sqrt(rating.phi ** 2 + sigma ** 2)
        # Step 7. Update the rating and RD to the new values, Mu' and Phi'.
        phi = 1. / math.sqrt(1 / phi_star ** 2 + 1 / variance)
        mu = rating.mu + phi ** 2 * (difference / variance)
        # Step 8. Convert ratings and RD's back to original scale.
        return self.scale_up(self.create_rating(mu, phi, sigma))
    
    
#Fonction ajustée pour récupérer les variations de points
    
    def rate_1vs1(self, rating1, rating2, winner=True):
       """Met à jour les classements pour un match 1 contre 1.

   rating1: Classement du joueur 1.
   rating2: Classement du joueur 2.
   winner: True si le joueur 1 gagne, False si le joueur 2 gagne.
   """
       if winner:
           rated1, rated2 = self.rate(rating1, [(WIN, rating2)]), self.rate(rating2, [(LOSS, rating1)])
       else:
           rated1, rated2 = self.rate(rating1, [(LOSS, rating2)]), self.rate(rating2, [(WIN, rating1)])
       
       delta_p1 = rated1.mu - rating1.mu  #Calcule la variation de points suite au match , afin de pouvoir appliquer les bonus /malus dessus 
       delta_p2 = rated2.mu - rating2.mu

       return rated1, rated2, delta_p1, delta_p2
        
        
#Nouvelle fonction : 
    
    def calculate_points(self, match):
        """
        Calcule les points pour un match en prenant en compte différents paramètres.
        """
        player1_id = match['Player1Id']
        player2_id = match['Player2Id']
        winner_id = match['WinnerId']
        match_round = match['Round']  # Remplace 'round' par 'match_round'
        grade = match['Grade']
        retired_id = match['RetiredId']
        walkover_id = match['WalkoverId']

        # Récupérer les points actuels des joueurs
        rating_p1 = self.player_ratings.get(player1_id, self.create_rating())
        rating_p2 = self.player_ratings.get(player2_id, self.create_rating())

        # Calcul des nouveaux ratings et des variations de points
        if winner_id == player1_id:
            new_rating_p1, new_rating_p2, delta_p1, delta_p2 = self.rate_1vs1(rating_p1, rating_p2, winner=True)
        else:
            new_rating_p1, new_rating_p2, delta_p1, delta_p2 = self.rate_1vs1(rating_p1, rating_p2, winner=False)

        # Bonus pour les outsiders
        if abs(rating_p1.mu - rating_p2.mu) > 250:
            outsider_bonus = 0.1
            if winner_id == player1_id:
                delta_p1 += delta_p1 * outsider_bonus
            elif winner_id == player2_id:
                delta_p2 += delta_p2 * outsider_bonus

        

        # Pondération selon le grade
        grade_coefficients = {1: 1.5, 2: 1.2, 3: 1.0}
        grade_multiplier = grade_coefficients.get(grade, 1.0)
        delta_p1 *= grade_multiplier
        delta_p2 *= grade_multiplier

        # Bonus par round
        round_bonuses = {
            'Quarter final': 0.15,
            'Semi final': 0.25,
            'Final': 0.35
        }
        
        round_bonus = round_bonuses.get(match_round, 0.0)
        delta_p1 += delta_p1 * round_bonus
        delta_p2 += delta_p2 * round_bonus

        # Mise à jour des points des joueurs
        new_rating_p1.mu += delta_p1
        new_rating_p2.mu += delta_p2
        
        
        # Pénalités pour forfaits ou abandons
        penalty_abandon = 40  # Pénalité pour abandon
        penalty_forfait = 80  # Pénalité pour forfait
        
        if retired_id == player1_id:  # Abandon du joueur 1
            new_rating_p1.mu -= penalty_abandon
            
        elif walkover_id == player1_id:  # Forfait du joueur 1
            new_rating_p1.mu -= penalty_forfait
        
        if retired_id == player2_id:  # Abandon du joueur 2
            new_rating_p2.mu -= penalty_abandon
        elif walkover_id == player2_id:  # Forfait du joueur 2
            new_rating_p2.mu -= penalty_forfait

        # Mise à jour des scores
        self.player_ratings[player1_id] = new_rating_p1
        self.player_ratings[player2_id] = new_rating_p2

        return new_rating_p1.mu, new_rating_p2.mu
    
    
    
    
    
    
    
    
