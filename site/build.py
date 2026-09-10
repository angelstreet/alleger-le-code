import json, re, pathlib, sys

root = pathlib.Path(__file__).resolve().parent.parent
LEGI = 'https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006072050/'
CODE_URL = 'https://www.legifrance.gouv.fr/codes/texte_lc/LEGITEXT000006072050'


class Topic:
    def __init__(self, id, name, title, lede, share, fr_file, ch_file, fr_scope, ch_scope, note=''):
        self.id, self.name, self.title, self.lede, self.share = id, name, title, lede, share
        self.fr = json.load(open(root / 'data' / fr_file))
        self.ch = json.load(open(root / 'data' / ch_file))
        self.fr_scope, self.ch_scope, self.note = fr_scope, ch_scope, note
        self.fr_arts = {a['num']: a for s in self.fr['sections'] for a in s['articles']}
        self.ch_arts = {a['num'].replace('Art. ', ''): a for s in self.ch['sections'] for a in s['articles']}
        self.rows = []

    def fr_chapter(self, *chs):
        n = w = 0
        for a in self.fr_arts.values():
            m = re.match(r'[LRD]\*?(\d{4})', a['num'])
            if m and m.group(1) in chs:
                n += 1; w += a['words']
        return n, w

    def fr_match(self, prefixes, path_re=None, exclude_re=None):
        """Count articles by number prefix, optionally restricted by a regex on the section path."""
        n = w = 0
        for s in self.fr['sections']:
            if path_re and not re.search(path_re, s['path']): continue
            if exclude_re and re.search(exclude_re, s['path']): continue
            for a in s['articles']:
                m = re.match(r'[LRD]\*?(\d{4})', a['num'])
                if m and m.group(1) in prefixes:
                    n += 1; w += a['words']
        return n, w

    def chapter_url(self, ch):
        for s in self.fr['sections']:
            if s['part'] == 'L' and any(re.match(r'L' + ch, a['num']) for a in s['articles']):
                return LEGI + s['id'] + '/'
        return CODE_URL

    def fr_sel(self, nums):
        return [{'num': n, 'url': self.fr_arts[n]['url'], 'text': self.fr_arts[n]['text']} for n in nums]

    def ch_sel(self, nums):
        out = []
        for n in nums:
            if n not in self.ch_arts:
                print(f'  ! CH article {n} missing in {self.id}', file=sys.stderr); continue
            a = self.ch_arts[n]
            out.append({'num': 'Art. ' + n, 'url': a['url'], 'text': a['text']})
        return out, len(out), sum(self.ch_arts[n]['words'] for n in nums if n in self.ch_arts)

    def row(self, id, q, title, fr_ch, fr_refs, fr_rule, fr_key, ch_nums, ch_refs, ch_rule, verdict, target, plan, fr_url=None):
        if isinstance(fr_ch, tuple): n, w = fr_ch; fr_ch = None
        else: n, w = self.fr_chapter(*fr_ch) if fr_ch else (0, 0)
        arts, cn, cw = self.ch_sel(ch_nums) if ch_nums else ([], 0, 0)
        self.rows.append({
            'id': id, 'q': q, 'title': title,
            'fr': {'n': n, 'w': w, 'refs': fr_refs, 'rule': fr_rule, 'arts': self.fr_sel(fr_key),
                   'url': fr_url or (self.chapter_url(fr_ch[0]) if fr_ch else CODE_URL)},
            'ch': {'n': cn, 'w': cw, 'refs': ch_refs, 'rule': ch_rule, 'arts': arts,
                   'url': arts[0]['url'] if arts else 'https://www.fedlex.admin.ch/eli/cc/27/317_321_377/fr'},
            'verdict': verdict, 'target': target, 'plan': plan,
        })

    def check(self):
        fn, fw = sum(r['fr']['n'] for r in self.rows), sum(r['fr']['w'] for r in self.rows)
        cn, cw = sum(r['ch']['n'] for r in self.rows), sum(r['ch']['w'] for r in self.rows)
        ft, ct = self.fr['topic_totals'], self.ch['topic_totals']
        assert (fn, fw) == (ft['articles_total'], ft['words_total']), (self.id, 'FR', fn, fw, ft)
        assert (cn, cw) == (ct['articles'], ct['words']), (self.id, 'CH', cn, cw, ct)
        print(f'{self.id}: FR {fn}/{fw}  CH {cn}/{cw}  target {sum(r["target"] for r in self.rows)}')

    def out(self):
        ft, ct = self.fr['topic_totals'], self.ch['topic_totals']
        return {'id': self.id, 'name': self.name, 'title': self.title, 'lede': self.lede, 'share': self.share,
                'fr': {'n': ft['articles_total'], 'w': ft['words_total'], 'scope': self.fr_scope, 'url': self.fr['sections'][0]['url'] if 'url' in self.fr['sections'][0] else LEGI + self.fr['sections'][0]['id'] + '/'},
                'ch': {'n': ct['articles'], 'w': ct['words'], 'scope': self.ch_scope, 'url': self.ch['sections'][0]['articles'][0]['url']},
                'note': self.note, 'rows': self.rows}


# ---------------------------------------------------------------- Topic 1
t1 = Topic('licenciement', 'Licenciement', 'Licencier un salarié en CDI',
           'Tout ce que la loi dit sur la fin d’un contrat à durée indéterminée, à périmètre égal.',
           'Licencier un salarié en CDI : 356 articles de loi en France, 29 en Suisse.',
           'fr_licenciement.json', 'ch_licenciement.json',
           'Code du travail, Livre II, Titre III « Rupture du contrat de travail à durée indéterminée », parties législative (L) et réglementaire (R, D)',
           'Code des obligations, art. 334 à 339c « Fin des rapports de travail »')

t1.row('motiver', 'Question 1', 'Décider et motiver le licenciement',
    ['1231', '1232'], 'L1231-1 → L1232-14, R1232, D1232',
    '<b>Cause réelle et sérieuse</b> obligatoire. Convocation à un entretien préalable (≥ 5 jours ouvrables), assistance par un conseiller, lettre recommandée motivée envoyée ≥ 2 jours après l’entretien, modèles ministériels.',
    ['L1232-1', 'L1232-2', 'L1232-6'],
    ['335', '337', '337a', '337b', '337c', '337d'], 'CO art. 335, 337 à 337d',
    '<b>Chacun peut résilier.</b> Le motif est donné par écrit si l’autre partie le demande. Résiliation immédiate possible pour justes motifs, appréciés par le juge.',
    ['simp'], 8,
    ['<b>On garde</b> : la motivation écrite et l’exigence d’un motif réel, qui protègent contre l’arbitraire.',
     '<b>On simplifie</b> : un seul article pour la procédure (motif écrit, délai, assistance). Les modalités de convocation, les délais et les modèles sont renvoyés aux conventions de branche ou à un décret unique.',
     '<b>On supprime</b> : le statut du conseiller du salarié comme chapitre à part entière (L1232-7 à L1232-14) — l’assistance reste un droit, sans un chapitre dédié.'],
    fr_url=t1.chapter_url('1232'))

t1.row('eco', 'Question 2', 'Licenciement économique et licenciement collectif',
    ['1233'], 'L1233-1 → L1233-91, R1233, D1233',
    '<b>109 articles de loi</b> et 64 de règlement : définition sur quatre indicateurs, obligation de reclassement, ordre des licenciements, contrat de sécurisation professionnelle, plan de sauvegarde de l’emploi homologué par l’administration, congé de reclassement, revitalisation des bassins d’emploi.',
    ['L1233-3', 'L1233-4', 'L1233-61'],
    ['335d', '335e', '335f', '335g', '335h', '335i', '335j', '335k'], 'CO art. 335d à 335k',
    '<b>Huit articles.</b> Seuils (10 salariés, 10 %, 30), consultation des travailleurs, notification à l’office cantonal, plan social obligatoire dès 250 salariés et 30 licenciements.',
    ['simp', 'deleg'], 20,
    ['<b>On garde</b> : la définition du motif économique, les seuils, la consultation du CSE, la notification à l’administration, le plan social au-delà d’un seuil.',
     '<b>On délègue aux branches et à l’assurance-chômage</b> : reclassement, contrat de sécurisation professionnelle, congé de reclassement, revitalisation — des dispositifs utiles qui n’ont pas à être écrits dans la loi article par article.',
     '<b>On fusionne</b> : petit et grand licenciement collectif en un régime unique à seuils, comme en Suisse. 173 articles deviennent une vingtaine.'])

t1.row('preavis', 'Question 3', 'Préavis, indemnité et documents de fin de contrat',
    ['1234'], 'L1234-1 → L1234-20, R1234, D1234',
    '<b>Préavis</b> d’un mois (6 mois à 2 ans d’ancienneté) puis deux mois. <b>Indemnité légale</b> dès 8 mois. Certificat de travail, reçu pour solde de tout compte, attestation pour France Travail.',
    ['L1234-1', 'L1234-9', 'L1234-20'],
    ['335a', '335b', '335c', '338', '338a', '339', '339a', '339b', '339c'], 'CO art. 335a à 335c, 338 à 339c',
    '<b>Préavis</b> d’un, deux ou trois mois selon l’ancienneté, modifiable par convention collective. Pas d’indemnité légale, sauf après 20 ans de service à partir de 50 ans. Restitution, exigibilité des créances, décès.',
    ['keep'], 12,
    ['<b>On garde</b> : les durées de préavis, l’indemnité légale de licenciement — une spécificité française qui n’existe pas en Suisse et que cette feuille de route ne propose pas de retirer.',
     '<b>On simplifie</b> : un chapitre unique, réécrit en langage courant, qui fusionne loi et règlement sur les documents de fin de contrat.'])

t1.row('contester', 'Question 4', 'Contester un licenciement',
    ['1235'], 'L1235-1 → L1235-17, R1235, D1235',
    '<b>Barème</b> d’indemnités par ancienneté (jusqu’à 20 mois), nullités (harcèlement, discrimination, grossesse…), remboursement des allocations à France Travail, conciliation forfaitaire, régimes distincts selon la taille de l’entreprise.',
    ['L1235-1', 'L1235-3'],
    ['336', '336a', '336b'], 'CO art. 336 à 336b',
    '<b>Congé abusif</b> : une liste de motifs interdits ; indemnité fixée par le juge, plafonnée à six mois de salaire ; opposition écrite avant la fin du préavis.',
    ['simp'], 8,
    ['<b>On garde</b> : le barème (déjà l’esprit de l’art. 336a suisse), la nullité pour discrimination et harcèlement.',
     '<b>On simplifie</b> : un article pour les nullités au lieu de sept, un seul régime quelle que soit la taille de l’entreprise, suppression des cas particuliers devenus lettre morte.'])

t1.row('protection', 'Question 5', 'Protection pendant la maladie, la grossesse, le service',
    None, 'Hors de ce titre : L1225-4 (maternité), L1226-9 (accident, maladie professionnelle)…',
    '<b>Dispersé.</b> Les périodes pendant lesquelles on ne peut pas licencier existent, mais dans d’autres livres du Code, chacune avec sa propre rédaction.',
    [],
    ['336c', '336d'], 'CO art. 336c, 336d',
    '<b>Un seul article</b> liste les périodes protégées : service militaire, maladie ou accident (30, 90, 180 jours selon l’ancienneté), grossesse et 16 semaines après, service humanitaire.',
    ['add'], 2,
    ['<b>On ajoute</b> : un article unique regroupant toutes les périodes de protection contre le licenciement, sur le modèle de l’art. 336c suisse. Il remplace les rédactions éparses de plusieurs titres du Code.',
     '<b>Résultat</b> : un salarié ou un employeur trouve en une lecture ce qui est interdit et quand.'])

t1.row('rc', 'Question 6', 'Démission, retraite, rupture conventionnelle',
    ['1237'], 'L1237-1 → L1237-19-14, R1237, D1237',
    '<b>Démission</b>, mise à la retraite, départ volontaire, <b>rupture conventionnelle</b> individuelle (rétractation 15 jours, homologation) et <b>rupture conventionnelle collective</b> (accord validé par l’administration).',
    ['L1237-11', 'L1237-13', 'L1237-19'],
    [], 'Aucun article dédié',
    '<b>Rien de spécifique.</b> La démission est le congé donné par le travailleur (art. 335). L’accord de résiliation relève du droit général des contrats et de la jurisprudence.',
    ['keep'], 10,
    ['<b>On garde</b> : la rupture conventionnelle individuelle, une réussite française utilisée plusieurs centaines de milliers de fois par an, et sa garantie de consentement.',
     '<b>On fusionne</b> : la rupture conventionnelle collective avec le plan social de la question 2 — deux dispositifs pour un même objet.',
     '<b>On simplifie</b> : démission et retraite en deux articles.'])

t1.row('chantier', 'Question 7', 'Contrats de chantier et contrats à durée déterminée',
    ['1236'], 'L1236-7 → L1236-9',
    '<b>Fin de chantier</b> = cause réelle et sérieuse, avec la procédure du licenciement personnel.',
    ['L1236-8'],
    ['334'], 'CO art. 334',
    '<b>Un article</b> : le contrat de durée déterminée prend fin sans congé ; au-delà de dix ans, chacun peut le résilier avec six mois de préavis.',
    ['keep'], 2, ['<b>On garde</b>, en réduisant les renvois croisés.'])

t1.row('penal', 'Question 8', 'Sanctions pénales',
    ['1238'], 'L1238-1 → L1238-5, R1238',
    '<b>Peines d’emprisonnement et amendes</b> pour entrave au conseiller du salarié, non-respect des procédures de licenciement collectif, défaut de certificat.',
    ['L1238-1'],
    [], 'Aucune disposition pénale',
    '<b>Aucune.</b> Les manquements se règlent par l’indemnité (art. 336a) et le droit civil ; le droit pénal général reste applicable à la fraude.',
    ['drop'], 0,
    ['<b>On supprime</b> : le chapitre pénal spécifique. Les infractions graves relèvent déjà du Code pénal ; les manquements de procédure sont sanctionnés par l’indemnité due au salarié.',
     '<b>On renvoie</b> les amendes administratives vers un article général de sanctions, commun à tout le Code.'])

t1.check()

# ---------------------------------------------------------------- Topic 2
topics = [t1]
if (root / 'data/ch_temps_travail.json').exists():
    t2 = Topic('temps-travail', 'Temps de travail', 'Durée du travail, repos et jours fériés',
               'Combien d’heures, quand, avec quelles pauses et quels jours de repos : les règles que chaque planning doit respecter.',
               'Temps de travail et repos : {fr} articles de loi en France, {ch} en Suisse.',
               'fr_temps_travail.json', 'ch_temps_travail.json',
               'Code du travail, 3e partie, Livre Ier, Titres II « Durée du travail » et III « Repos et jours fériés » (L3121 à L3134), parties L, R et D',
               'Loi fédérale sur le travail (LTr), chapitre 2 « Durée du travail et du repos », art. 9 à 28 + Code des obligations art. 321c',
               note='<b>À lire avec une réserve.</b> En Suisse, le détail des pauses, du travail de nuit et des autorisations est dans l’ordonnance OLT 1, non comptée ici. L’écart réel est donc plus faible que le chiffre brut — mais la loi elle-même reste lisible en une heure.')
    t2.share = t2.share.format(fr=t2.fr['topic_totals']['articles_total'], ch=t2.ch['topic_totals']['articles'])

    t2.row('duree', 'Question 1', 'Durée du travail, heures supplémentaires, forfaits',
        ['3121'], 'L3121-1 → L3121-69, R3121, D3121',
        '<b>35 heures</b> légales, 10 h par jour, 48 h par semaine (44 h en moyenne sur 12 semaines). Heures supplémentaires majorées de 25 % puis 50 %, contingent, repos compensateur, forfaits en heures ou en jours, astreintes. Depuis 2016, chaque règle est écrite trois fois : ordre public, champ de la négociation, dispositions supplétives.',
        ['L3121-27', 'L3121-18', 'L3121-36'],
        ['9', '10', '11', '12', '13', '24', '25', '26', '27', '28', '321c'], 'LTr art. 9 à 13, 24 à 28 ; CO art. 321c',
        '<b>45 ou 50 heures</b> maximum par semaine selon le secteur, pas de durée légale. Travail supplémentaire limité à 2 h par jour et 170 h par an, payé +25 % ou compensé en temps. Travail de jour de 6 h à 20 h. Travail continu et équipes en trois articles.',
        ['simp', 'deleg'], 20,
        ['<b>On garde</b> : les 35 heures et les durées maximales — ce site ne propose pas de toucher à la durée légale — la majoration des heures supplémentaires, le repos compensateur, le forfait-jours.',
         '<b>On simplifie</b> : une règle écrite une fois, suivie de « sauf accord collectif », au lieu du triptyque ordre public / négociation / supplétif qui triple le texte depuis 2016.',
         '<b>On délègue aux branches</b> : modalités d’astreinte, décompte, aménagement du temps sur plusieurs semaines.'])

    t2.row('nuit', 'Question 2', 'Travail de nuit',
        ['3122'], 'L3122-1 → L3122-24, R3122',
        '<b>Nuit = 21 h à 6 h</b> (ou 9 h consécutives). Recours exceptionnel, justifié, par accord collectif ou autorisation de l’inspection. 8 h par poste, 40 h par semaine sur 12 semaines, contreparties en repos, suivi médical, secteurs spécifiques (presse, spectacle…).',
        ['L3122-1', 'L3122-6'],
        ['16', '17', '17a', '17b', '17c', '17d', '17e'], 'LTr art. 16 à 17e',
        '<b>Interdit sauf autorisation</b> (besoin indispensable), 9 h de travail dans un espace de 10 h, compensation de 10 % en temps, examen médical, mesures supplémentaires pour le travail de nuit régulier.',
        ['simp'], 8,
        ['<b>On garde</b> : la définition, la limite par poste, les contreparties et le suivi médical.',
         '<b>On simplifie</b> : un seul régime d’autorisation (accord collectif ou inspection), suppression des variantes par secteur, fin du triptyque.'])

    t2.row('partiel', 'Question 3', 'Temps partiel et travail intermittent',
        ['3123'], 'L3123-1 → L3123-38, R3123, D3123',
        '<b>Durée minimale de 24 h</b> par semaine sauf dérogations, heures complémentaires majorées, priorité d’accès au temps plein, mentions obligatoires du contrat, travail intermittent.',
        ['L3123-7', 'L3123-8'],
        [], 'Aucun article dédié',
        '<b>Rien de spécifique</b> : le temps partiel est un contrat de travail comme un autre, aux conditions convenues, sous les plafonds de la LTr.',
        ['keep'], 10,
        ['<b>On garde</b> : la durée minimale et la majoration des heures complémentaires, protections françaises sans équivalent suisse.',
         '<b>On simplifie</b> : un régime écrit une fois ; le travail intermittent renvoyé aux branches qui l’utilisent.'])

    t2.row('repos', 'Question 4', 'Repos quotidien et pauses',
        ['3131'], 'L3131-1 → L3131-3, D3131 (pauses : L3121-16 et -17, comptées à la question 1)',
        '<b>11 heures</b> consécutives de repos, dérogations par accord ou décret. Pause de 20 minutes après 6 heures.',
        ['L3131-1'],
        ['15', '15a'], 'LTr art. 15, 15a',
        '<b>Pauses</b> de 15, 30 ou 60 minutes selon la journée (plus de 5 h 30, 7 h, 9 h). <b>11 heures</b> de repos quotidien, réductibles à 8 h une fois par semaine.',
        ['keep'], 3,
        ['<b>On garde</b> tel quel : les deux droits sont déjà presque identiques.',
         '<b>On simplifie</b> : les sept articles de décret sur les dérogations en un seul.'])

    t2.row('dimanche', 'Question 5', 'Repos hebdomadaire et travail du dimanche',
        ['3132'], 'L3132-1 → L3132-31, R3132, D3132',
        '<b>35 heures</b> de repos par semaine, le dimanche. Puis 60 articles de dérogations : établissements listés par décret, commerces alimentaires, zones touristiques et commerciales, gares, « dimanches du maire », Paris, contreparties, autorisations préfectorales.',
        ['L3132-1', 'L3132-3', 'L3132-12'],
        ['18', '19', '20', '21', '22'], 'LTr art. 18 à 22',
        '<b>Interdit le dimanche</b> sauf autorisation (besoin indispensable) ; repos compensatoire ; demi-journée de congé hebdomadaire ; interdiction de remplacer le repos par de l’argent.',
        ['simp', 'deleg'], 10,
        ['<b>On garde</b> : le repos hebdomadaire de 35 h, le principe du dimanche, les contreparties pour le salarié.',
         '<b>On simplifie</b> : un régime unique d’autorisation avec contreparties, comme l’art. 19 LTr, à la place de la liste des dérogations accumulées depuis un siècle.',
         '<b>On délègue</b> : la liste des activités autorisées le dimanche à un décret unique et aux accords de branche ou de territoire.'])

    t2.row('feries', 'Question 6', 'Jours fériés',
        ['3133'], 'L3133-1 → L3133-12, D3133',
        '<b>Onze jours fériés</b>, seul le 1<sup>er</sup> mai obligatoirement chômé et payé double s’il est travaillé. Journée de solidarité, régime des jeunes travailleurs.',
        ['L3133-1', 'L3133-4'],
        ['20a'], 'LTr art. 20a',
        '<b>Un article</b> : la fête nationale et jusqu’à huit jours fériés cantonaux sont assimilés au dimanche.',
        ['keep'], 4,
        ['<b>On garde</b> : la liste et le 1<sup>er</sup> mai.',
         '<b>On simplifie</b> : la journée de solidarité fusionnée dans un article, le reste renvoyé aux branches.'])

    t2.row('alsace', 'Question 7', 'Droit local en Alsace-Moselle',
        ['3134'], 'L3134-1 → L3134-16, R3134, D3134',
        '<b>Un régime distinct</b> du repos dominical et des jours fériés pour trois départements, hérité de 1892, avec ses propres dérogations, autorisations et sanctions.',
        ['L3134-1'],
        [], 'Aucun article : les cantons fixent leurs jours fériés (art. 20a)',
        '<b>Le fédéralisme</b> règle la question en une phrase : chaque canton choisit ses jours fériés dans le cadre de l’art. 20a.',
        ['simp'], 4,
        ['<b>On garde</b> : le droit local, garanti par le Conseil constitutionnel.',
         '<b>On simplifie</b> : le Code renvoie en un article au droit local au lieu de le récrire ; les dérogations locales rejoignent le régime unique de la question 5.'])

    t2.check()
    topics.append(t2)

# ---------------------------------------------------------------- Topic 3
if (root / 'data/ch_conges.json').exists():
    t3 = Topic('conges', 'Congés', 'Congés payés, congés spéciaux, maternité et paternité',
               'Tous les jours où l’on ne travaille pas tout en restant salarié : vacances, événements de la vie, naissance, engagement, projets.',
               'Congés et vacances : {fr} articles de loi en France, {ch} en Suisse.',
               'fr_conges.json', 'ch_conges.json',
               'Code du travail, 3e partie, Livre Ier, Titres IV « Congés payés et autres congés » et V « Compte épargne-temps » (L3141 à L3154) + Livre II, Titre II, Chapitre V « Maternité, paternité, adoption » (L1225), parties L, R et D',
               'Code des obligations art. 329 à 329j « Jours de congé, vacances et congés » + Loi sur le travail art. 35 à 36 (grossesse, maternité, obligations familiales)',
               note='<b>Lire la générosité à part.</b> La Suisse accorde 4 semaines de vacances (5 avant 20 ans), 14 semaines de maternité et 2 semaines à l’autre parent — moins qu’en France. Ce sujet compare la lisibilité des textes, pas les droits : la feuille de route conserve les durées françaises.')
    t3.share = t3.share.format(fr=t3.fr['topic_totals']['articles_total'], ch=t3.ch['topic_totals']['articles'])
    S = lambda k: t3.fr_match(['3142'], path_re=r'> Section %d :' % k)

    t3.row('payes', 'Question 1', 'Congés payés',
        ['3141'], 'L3141-1 → L3141-33, R3141, D3141',
        '<b>2,5 jours ouvrables par mois</b>, soit 5 semaines. Période de référence, décompte en jours ouvrables, fractionnement et jours supplémentaires, ordre des départs, indemnité de congés, caisses de congés payés du bâtiment. Chaque règle en trois couches depuis 2016.',
        ['L3141-3', 'L3141-13'],
        ['329a', '329b', '329c', '329d'], 'CO art. 329a à 329d',
        '<b>4 semaines</b> par an (5 avant 20 ans), au prorata, deux semaines consécutives au moins, date fixée par l’employeur en tenant compte des vœux, salaire maintenu, remplacement en argent interdit.',
        ['keep'], 10,
        ['<b>On garde</b> : les 5 semaines, l’indemnité de congés, le droit à deux semaines consécutives.',
         '<b>On simplifie</b> : le décompte en jours ouvrés plutôt qu’ouvrables (fin des calculs de samedis), les règles de fractionnement renvoyées aux branches, les caisses de congés payés vers la convention du bâtiment.'])

    t3.row('famille', 'Question 2', 'Événements familiaux, proches aidants, sabbatique',
        S(1), 'L3142-1 → L3142-35, R3142, D3142 (section 1)',
        '<b>Mariage, naissance, décès</b> (jours fixés par la loi), congé de solidarité familiale, congé de proche aidant (indemnisé), congé sabbatique : chacun avec ses conditions d’ancienneté, délais de prévenance, report, retour.',
        ['L3142-1', 'L3142-16'],
        ['329', '329h', '329i'], 'CO art. 329, 329h, 329i',
        '<b>Les heures et jours de congé usuels</b> sont accordés (art. 329) ; congé payé de 3 jours par cas et 10 par an pour un proche malade (329h) ; 14 semaines pour un enfant gravement atteint (329i).',
        ['simp'], 6,
        ['<b>On garde</b> : les durées légales pour les événements familiaux et le congé de proche aidant indemnisé.',
         '<b>On simplifie</b> : un article pour les événements familiaux, un pour l’aide à un proche, un pour le sabbatique ; les conditions d’ancienneté et de prévenance renvoyées aux branches.'])

    t3.row('engagement', 'Question 3', 'Congés pour engagement associatif, politique, militant',
        S(2), 'L3142-36 → L3142-103, R3142, D3142 (section 2)',
        '<b>Quinze congés distincts</b> : formation de cadres de jeunesse, mutualiste, représentation, solidarité internationale, catastrophe naturelle, réserviste, sapeur-pompier, juré, élu local, candidat, formation syndicale… chacun avec ses articles de loi et ses décrets.',
        ['L3142-54', 'L3142-60'],
        ['329e'], 'CO art. 329e',
        '<b>Un seul congé</b> pour les activités de jeunesse extrascolaires : 5 jours par an, non payés, jusqu’à 30 ans. Le reste relève du contrat ou de la convention collective.',
        ['simp', 'deleg'], 6,
        ['<b>On garde</b> : le principe d’un droit à s’absenter pour un engagement d’intérêt général.',
         '<b>On simplifie</b> : un régime unique « congé d’engagement » — un article de principe, une liste des engagements ouvrant droit fixée par décret, les durées et le maintien du salaire par branche.',
         '<b>On supprime</b> : 118 articles qui répètent la même mécanique quinze fois.'])

    t3.row('projet', 'Question 4', 'Créer une entreprise, enseigner, chercher',
        tuple(map(sum, zip(S(3), S(4), t3.fr_match(['3142'], exclude_re=r'> Section \d')))),
        'L3142-105 → L3142-131, D3142 (sections 3 et 4)',
        '<b>Congé ou temps partiel</b> pour créer ou reprendre une entreprise, congé d’enseignement ou de recherche : un an, prolongeable, avec réintégration garantie.',
        ['L3142-105'],
        [], 'Aucun article',
        '<b>Rien de spécifique</b> : un tel congé se négocie dans le contrat ou la convention collective.',
        ['deleg'], 4,
        ['<b>On délègue aux branches et aux entreprises</b> : la loi ne garde que le principe d’un congé non rémunéré avec droit au retour ; durées et conditions par accord.'])

    t3.row('maternite', 'Question 5', 'Grossesse et congé de maternité',
        t3.fr_match(['1225'], path_re=r'> Section 1 :'), 'L1225-1 → L1225-34, R1225, D1225 (section 1)',
        '<b>16 semaines</b> (plus selon le rang de l’enfant et les naissances multiples), protection contre le licenciement, affectation temporaire, autorisations d’absence pour examens, allaitement, garantie de rémunération au retour.',
        ['L1225-17', 'L1225-4'],
        ['329f', '35', '35a', '35b'], 'CO art. 329f ; LTr art. 35 à 35b',
        '<b>14 semaines</b> après l’accouchement (prolongées si le nouveau-né est hospitalisé), interdiction de travailler 8 semaines après la naissance, aménagement du poste, temps d’allaitement rémunéré.',
        ['keep'], 10,
        ['<b>On garde</b> : les 16 semaines, la protection contre le licenciement, l’allaitement, la garantie de rémunération.',
         '<b>On simplifie</b> : un chapitre lisible en une page ; les cas particuliers (naissances multiples, décès de la mère) en un article.'])

    t3.row('parents', 'Question 6', 'Paternité, adoption, congé parental',
        t3.fr_match(['1225'], exclude_re=r'> Section 1 :'), 'L1225-35 → L1225-72, R1225, D1225 (sections 2 à 5)',
        '<b>25 jours</b> de paternité, congé d’adoption, congé parental d’éducation jusqu’aux 3 ans de l’enfant, congé pour enfant malade, congé de présence parentale : cinq régimes, chacun avec sa demande, son retour, sa protection.',
        ['L1225-35', 'L1225-47'],
        ['329g', '329gbis', '329j', '36', '36a'], 'CO art. 329g, 329g bis, 329j ; LTr art. 36, 36a',
        '<b>2 semaines</b> pour l’autre parent (le reste du congé de maternité s’il y a décès de la mère), 2 semaines d’adoption, et un article sur les responsabilités familiales : horaires adaptés, pause de midi, jusqu’à 3 jours pour un enfant malade.',
        ['keep'], 10,
        ['<b>On garde</b> : toutes les durées, y compris le congé parental d’éducation qui n’existe pas en Suisse.',
         '<b>On simplifie</b> : les mécaniques communes (demande, protection, retour, ancienneté) écrites une fois pour les cinq congés.'])

    t3.row('cet', 'Question 7', 'Compte épargne-temps',
        ['3151', '3152', '3153', '3154'], 'L3151-1 → L3153-2, D3154',
        '<b>Épargner des jours</b> de repos ou de rémunération pour les utiliser plus tard, par accord collectif ; garantie des droits, liquidation.',
        ['L3151-2'],
        [], 'Aucun article',
        '<b>Rien de spécifique</b> : le CO permet de reporter des vacances dans certaines limites ; le reste est conventionnel.',
        ['keep'], 3,
        ['<b>On garde</b> : un outil français utile, en trois articles au lieu de seize.'])

    t3.row('penal3', 'Question 8', 'Sanctions pénales',
        ['3143'], 'R3143-1 → R3143-3',
        '<b>Contraventions</b> pour non-respect des congés payés et des congés spéciaux.',
        [],
        [], 'Aucune disposition pénale',
        '<b>Aucune</b> : le salarié fait valoir son droit ; l’inspection dispose des sanctions générales de la LTr.',
        ['drop'], 0,
        ['<b>On supprime</b> : rattaché à l’article général de sanctions, comme pour les autres sujets.'])

    t3.check()
    topics.append(t3)

# ---------------------------------------------------------------- Topic 4
if (root / 'data/ch_sante.json').exists() and (root / 'data/fr_sante.json').exists():
    t4 = Topic('sante', 'Santé et sécurité', 'Santé et sécurité : les principes et les obligations',
               'Ce que l’employeur doit faire pour protéger la santé, ce que le salarié doit respecter, et qui peut dire non à un travail dangereux.',
               'Santé et sécurité au travail, rien que les principes : {fr} articles de loi en France, {ch} en Suisse.',
               'fr_sante.json', 'ch_sante.json',
               'Code du travail, 4e partie « Santé et sécurité au travail », Livre Ier « Dispositions générales » (L4111 à L4163), parties L, R et D',
               'Code des obligations art. 328 ; Loi sur le travail art. 6 à 8 et 29 à 32 ; Loi sur l’assurance-accidents art. 81 à 88',
               note='<b>Deux réserves.</b> Côté suisse, le détail est dans les ordonnances OLT 3 (42 articles) et OPA (132 articles), non comptées ici. Côté français, seul le Livre Ier est compté : les sept autres livres de la 4e partie (lieux de travail, équipements, risques chimiques, bâtiment, services de santé au travail, contrôle) s’y ajoutent. La comparaison porte sur les principes, pas sur les règles techniques.')
    t4.share = t4.share.format(fr=t4.fr['topic_totals']['articles_total'], ch=t4.ch['topic_totals']['articles'])

    t4.row('principes', 'Question 1', 'Obligations de l’employeur et des travailleurs',
        ['4111', '4121', '4122'], 'L4111-1 → L4122-2, R4121',
        '<b>Obligation générale de sécurité</b>, neuf principes de prévention, évaluation des risques (document unique), obligations du salarié de prendre soin de sa santé et de celle des autres, champ d’application.',
        ['L4121-1', 'L4121-2', 'L4122-1'],
        ['328', '6', '81', '82', '82a', '83'], 'CO art. 328 ; LTr art. 6 ; LAA art. 81 à 83',
        '<b>L’employeur protège la santé et la personnalité</b> du travailleur (CO 328), prend les mesures que l’état de la technique permet et fait participer les travailleurs (LTr 6) ; prévention des accidents et maladies professionnels, prescriptions du Conseil fédéral (LAA 81 à 83).',
        ['keep'], 6,
        ['<b>On garde</b> : l’obligation générale, les principes de prévention, l’évaluation des risques, l’obligation du salarié.',
         '<b>On simplifie</b> : les cinq articles de décret sur le document unique fusionnés dans la loi en un article.'])

    t4.row('alerte', 'Question 2', 'Droit d’alerte et droit de retrait',
        ['4131', '4132', '4133'], 'L4131-1 → L4133-4, D4132, D4133',
        '<b>Danger grave et imminent</b> : le salarié alerte et peut se retirer sans sanction ni retenue ; alerte du représentant du personnel, registre ; alerte en matière de santé publique et d’environnement.',
        ['L4131-1', 'L4131-3'],
        [], 'Aucun article dédié',
        '<b>Rien de spécifique</b> : le refus d’un travail dangereux est couvert par la protection de la personnalité (CO 328) et par la protection contre le congé abusif (CO 336).',
        ['keep'], 3,
        ['<b>On garde</b> : le droit de retrait et l’absence de sanction — un acquis français qu’on n’efface pas.',
         '<b>On simplifie</b> : un article pour le droit de retrait, un pour l’alerte, un pour l’alerte environnementale.'])

    t4.row('formation', 'Question 3', 'Information et formation à la sécurité',
        ['4141', '4142', '4143'], 'L4141-1 → L4143-1, R4141, R4143',
        '<b>Formation pratique et appropriée</b> à l’embauche, au changement de poste, à la reprise ; vingt et un articles de décret sur son contenu (circulation, exécution du travail, conduite à tenir en cas d’accident).',
        ['L4141-2'],
        [], 'Aucun article dédié (LTr 6, al. 3 : informer et instruire)',
        '<b>Une phrase</b> : l’employeur informe et instruit les travailleurs de manière appropriée (LTr 6). Le détail est dans l’ordonnance OLT 3.',
        ['simp'], 4,
        ['<b>On garde</b> : l’obligation de former, aux trois moments clés.',
         '<b>On simplifie</b> : le contenu de la formation renvoyé à un décret unique ou aux branches ; 34 articles deviennent 4.'])

    t4.row('categories', 'Question 4', 'Femmes enceintes, jeunes, intérimaires et CDD',
        ['4151', '4152', '4153', '4154'], 'L4151-1 → L4154-4, R4152 à R4154, D4152 à D4154',
        '<b>Travaux interdits ou réglementés</b> pour les jeunes (avec dérogations), pour les femmes enceintes, pour les intérimaires et CDD (liste, formation renforcée, surveillance médicale), avec la procédure de dérogation et le rôle de l’inspection.',
        ['L4153-8', 'L4154-2'],
        ['29', '30', '31', '32'], 'LTr art. 29 à 32',
        '<b>Quatre articles</b> : âge minimum, protection particulière des jeunes, durée du travail et repos des jeunes, dérogations. Les travaux dangereux sont listés par ordonnance.',
        ['simp', 'deleg'], 8,
        ['<b>On garde</b> : les interdictions de travaux dangereux pour chaque catégorie et la formation renforcée des intérimaires.',
         '<b>On simplifie</b> : un article par catégorie ; les listes de travaux interdits dans un décret unique, comme l’ordonnance suisse.',
         '<b>On délègue</b> : les modalités de dérogation aux branches.'])

    t4.row('c2p', 'Question 5', 'Compte professionnel de prévention (pénibilité)',
        ['4161', '4162', '4163'], 'L4161-1 → L4163-22, R4162, R4163, D4161 à D4163',
        '<b>Six facteurs de risques</b>, déclaration, points, utilisation (formation, temps partiel, retraite anticipée), financement, contentieux : 94 articles pour un mécanisme de sécurité sociale logé dans le Code du travail.',
        ['L4161-1', 'L4163-1'],
        [], 'Aucun article',
        '<b>Rien dans le droit du travail</b> : la retraite anticipée des métiers pénibles relève des caisses de pension et des conventions collectives (le bâtiment part à 60 ans par CCT).',
        ['move'], 0,
        ['<b>On transfère</b> : le C2P entier vers le Code de la sécurité sociale, dont il relève (cotisations, points, retraite). Le Code du travail ne garde que l’obligation de prévenir les risques, déjà écrite à la question 1.'])

    t4.row('controle', 'Question 6', 'Contrôle préalable et financement de la prévention',
        None, 'Hors de ce livre : Livre II (locaux), Livre VIII (inspection), Code de la sécurité sociale (branche AT-MP)',
        '<b>Ailleurs dans le Code</b> : permis et conformité des locaux, inspection du travail, financement de la prévention par la cotisation accidents du travail.',
        [],
        ['7', '8', '84', '85', '86', '87', '87a', '88'], 'LTr art. 7, 8 ; LAA art. 84 à 88',
        '<b>Approbation des plans</b> et autorisation d’exploiter pour les entreprises industrielles ; organes d’exécution (CNA, inspections), financement par un supplément de prime.',
        ['keep'], 0,
        ['<b>Rien à ajouter</b> : la France règle cela dans d’autres livres. On note seulement qu’en Suisse la loi tient l’ensemble en huit articles.'])

    t4.check()
    topics.append(t4)

# ---------------------------------------------------------------- Code allégé (drafts)
allege = {}
for t in topics:
    f = root / f'data/code_allege_{t.id}.json'
    if not f.exists(): continue
    d = json.load(open(f))
    for a in d['articles']:
        a['replaces'] = [{'num': n, 'url': t.fr_arts[n]['url']} if n in t.fr_arts else {'num': n, 'url': CODE_URL} for n in a['replaces']]
    d['rows'] = {r['id']: r['title'] for r in t.rows}
    allege[t.id] = d
    print(f'{t.id}: code allégé {len(d["articles"])} articles, {len(d.get("removed", []))} removed groups')

# ---------------------------------------------------------------- Output
fr_code = t1.fr['code_totals']
data = {
    'code': {
        'fr': fr_code,
        'ch': {k: t1.ch['code_totals'].get(k) for k in ('co_titre10', 'ltr', 'co_whole')},
    },
    'topics': [t.out() for t in topics],
    'allege': allege,
    'upcoming': ['Représentation du personnel', 'Salaire et salaire minimum', 'Formation du contrat, CDD, intérim', 'Apprentissage et formation'],
}
if len(topics) > 1:
    data['code']['ch']['olt1'] = topics[1].ch['code_totals'].get('olt1')

payload = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
import os
sb = {'url': os.environ.get('SUPABASE_URL', ''), 'key': os.environ.get('SUPABASE_ANON_KEY', '')}
supabase = json.dumps(sb) if sb['url'] and sb['key'] else 'null'
tpl = open(root / 'site/template.html', encoding='utf-8').read()
out = tpl.replace('{{DATA}}', payload).replace('{{SUPABASE}}', supabase)
open(root / 'site/index.html', 'w', encoding='utf-8').write(out)
print('wrote', len(out), 'bytes;', len(topics), 'topics')
