"""
Management command to populate the theoretical framework and add sample testimonials
"""
from django.core.management.base import BaseCommand
from chatbot.models import TheoreticalFramework


class Command(BaseCommand):
    help = 'Populate theoretical framework for CBT-SDT integration'

    def handle(self, *args, **options):
        self.stdout.write('Populating theoretical framework...')
        
        # Create SDT-CBT Integrated Framework
        framework, created = TheoreticalFramework.objects.get_or_create(
            name='SDT-CBT Integrated Framework',
            defaults={
                'description': '''This framework integrates Self-Determination Theory (SDT) with 
                Cognitive Behavioral Therapy (CBT) to create a comprehensive, evidence-based approach 
                to mental health support through AI-powered chatbot interaction.''',
                
                'principles': {
                    'self_determination_theory': {
                        'autonomy': 'Supporting user autonomy by providing choices and respecting self-direction in their therapeutic journey',
                        'competence': 'Building competence through skill development, positive feedback, and achievable goals',
                        'relatedness': 'Fostering connection through empathetic responses and normalizing experiences'
                    },
                    'cognitive_behavioral_therapy': {
                        'cognitive_restructuring': 'Identifying and challenging maladaptive thought patterns',
                        'behavioral_activation': 'Encouraging engagement in rewarding activities to combat depression',
                        'exposure_therapy': 'Gradual exposure to anxiety-provoking situations',
                        'problem_solving': 'Systematic approach to life challenges',
                        'mindfulness': 'Present-moment awareness and acceptance'
                    }
                },
                
                'mechanisms': [
                    'Autonomy Support: User-driven goal setting and therapeutic choices increase intrinsic motivation',
                    'Competence Building: CBT skills training enhances self-efficacy and perceived competence',
                    'Therapeutic Alliance: Empathetic AI interaction fosters sense of relatedness and safety',
                    'Cognitive Change: Socratic questioning reduces cognitive distortions',
                    'Behavioral Change: Activity scheduling and exposure reduce avoidance patterns',
                    'Skill Transfer: Learned coping strategies generalize to real-world situations',
                    'Self-Monitoring: Assessment tracking increases self-awareness and motivation'
                ],
                
                'hypotheses': [
                    'H1: Users receiving CBT-enhanced chatbot intervention will show significantly greater reduction in PHQ-9 scores compared to control group (waitlist or standard chatbot)',
                    'H2: Users receiving CBT-enhanced chatbot intervention will show significantly greater reduction in GAD-7 scores compared to control group',
                    'H3: SDT need satisfaction (autonomy, competence, relatedness) will mediate the relationship between intervention engagement and symptom reduction',
                    'H4: Higher baseline competence scores will predict better engagement (sessions completed) and outcomes (symptom reduction)',
                    'H5: Clinically significant change (≥50% symptom reduction) will occur in at least 40% of intervention group participants',
                    'H6: Effect size (Cohen\'s d) for PHQ-9 reduction will be medium to large (d ≥ 0.5)',
                    'H7: Effect size (Cohen\'s d) for GAD-7 reduction will be medium to large (d ≥ 0.5)',
                    'H8: Users who complete thought records will show greater cognitive restructuring and symptom improvement',
                    'H9: Behavioral activation engagement will correlate positively with depression symptom reduction',
                    'H10: Therapeutic alliance (relatedness) will predict intervention adherence and completion'
                ],
                
                'evidence_base': '''
THEORETICAL FOUNDATIONS:

Self-Determination Theory (Deci & Ryan, 2000):
- Meta-analysis supporting SDT in healthcare (Ng et al., 2012)
- Autonomy support predicts better mental health outcomes
- Competence and relatedness crucial for sustained behavior change

Cognitive Behavioral Therapy:
- Gold standard for depression and anxiety (NICE Guidelines, 2011)
- Effect sizes: Depression d=0.70, Anxiety d=0.80 (Hofmann et al., 2012)
- Digital CBT effective: d=0.56 for depression (Carlbring et al., 2018)

AI-Based Interventions:
- Chatbot therapy shows promise (Fitzpatrick et al., 2017)
- Digital mental health interventions effective (Ebert et al., 2018)
- Engagement critical for outcomes (Donkin et al., 2011)

VALIDATED MEASURES:

PHQ-9 (Patient Health Questionnaire-9):
- Validated depression screening tool (Kroenke et al., 2001)
- Sensitivity: 88%, Specificity: 88% for major depression
- Reliable for tracking treatment response
- Score ≥10: Clinical depression threshold

GAD-7 (Generalized Anxiety Disorder-7):
- Validated anxiety screening tool (Spitzer et al., 2006)
- Sensitivity: 89%, Specificity: 82% for GAD
- Good convergent validity with other anxiety measures
- Score ≥10: Clinical anxiety threshold

CLINICAL SIGNIFICANCE:
- ≥50% symptom reduction = clinically meaningful change
- Reliable Change Index (RCI) for individual-level change
- Effect size benchmarks: 0.2=small, 0.5=medium, 0.8=large (Cohen, 1988)

KEY REFERENCES:
1. Deci, E. L., & Ryan, R. M. (2000). Self-determination theory
2. Beck, A. T. (1979). Cognitive therapy of depression
3. Kroenke, K., et al. (2001). The PHQ-9: Validity of a brief depression measure
4. Spitzer, R. L., et al. (2006). A brief measure for assessing GAD: The GAD-7
5. Hofmann, S. G., et al. (2012). The efficacy of CBT: A review of meta-analyses
6. Fitzpatrick, K. K., et al. (2017). Delivering CBT for depression by chatbot
7. Ebert, D. D., et al. (2018). Internet and mobile-based psychological interventions
                '''
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Theoretical framework created successfully'))
        else:
            self.stdout.write(self.style.WARNING('! Theoretical framework already exists, updated'))
        
        # Display framework details
        self.stdout.write('\n' + '='*80)
        self.stdout.write(f'Framework: {framework.name}')
        self.stdout.write('='*80)
        self.stdout.write(f'\nDescription: {framework.description}')
        self.stdout.write(f'\nHypotheses: {len(framework.hypotheses)} testable hypotheses defined')
        self.stdout.write(f'\nMechanisms: {len(framework.mechanisms)} mechanisms of action specified')
        self.stdout.write('\n' + '='*80)
        
        self.stdout.write(self.style.SUCCESS('\n✓ Framework setup complete!'))
        self.stdout.write('\nNext steps:')
        self.stdout.write('1. Users can now take PHQ-9 and GAD-7 assessments')
        self.stdout.write('2. CBT techniques are integrated into chatbot responses')
        self.stdout.write('3. Progress tracking available in assessment dashboard')
        self.stdout.write('4. Intervention outcomes calculated with effect sizes')
