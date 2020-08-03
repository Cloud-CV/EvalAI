import { Component, OnInit, Input } from '@angular/core';
import { GlobalService } from '../../../services/global.service';
import { ApiService } from '../../../services/api.service';
import { AuthService } from '../../../services/auth.service';
import { ChallengeService } from '../../../services/challenge.service';
import { Router, ActivatedRoute } from '@angular/router';

/**
 * Component Class
 */
@Component({
  selector: 'app-template-challenge-create-card',
  templateUrl: './template-challenge-create-card.component.html',
  styleUrls: ['./template-challenge-create-card.component.scss']
})
export class TemplateChallengeCreateCard implements OnInit {

  /**
   * template object
     It is of form:
     {
        "title": <title of the challenge template>,
        "image": <preview image of the challenge template>,
        "dataset": <string discribing the dataset>,
        "eval_criteria": <an array or list of strings which are the leaderboard metrics>,
        "phases": <number of challenge phases>,
        "splits": <number of dataset splits>,

     }
   */
  @Input() template: object;

  templateChallengeData = 
  {
    'tiitle': '',
    'description': null, // FIle
    'evaluation_details': null, // File
    'image': null, // File
    'submission_guidelines': null, // File
    'start_date': null,
    'end_date': null,
    'challenge_phases': [], // Init this through template in ngOnInit
    'dataset_splits': [], // Init this through template in ngOnInit
    };
  

  challengePhaseStructure = {
    'name': '',
    'description': null, // File
    'start_date': null,
    'end_date': null,
    'id': 'phase_'+'${i}'
  };

  datasetSplitsStructure = {
    'name': '',
    'id': 'split_''+${i}'
  }

  numOfPhases = template['phases']
  numOfSplits = template['splits']

  /**
   * Constructor.
   * @param route  ActivatedRoute Injection.
   * @param router  Router Injection.
   * @param globalService  GlobalService Injection.
   * @param authService  AuthService Injection.
   * @param apiService  ApiService Injection.
   * @param challengeService  ChallengeService Injection.
   */
  constructor(private globalService: GlobalService,
              private apiService: ApiService,
              private authService: AuthService,
              private challengeService: ChallengeService,
              private router: Router,
              private route: ActivatedRoute) { }

  /**
   * Component on initialized.
   */
  ngOnInit() {
    SELF = this;
    for(let i = 0; i<SELF.numOfPhases; i++){
      let phaseData = Object.assign({}, challengePhaseStructure);
      SELF.templateChallengeData['challenge_phases'].push(phaseData);
    }

    for(let i = 0; i<SELF.numOfSplits; i++){
      let splitData = Object.assign({}, datasetSplitsStructure);
      SELF.templateChallengeData['dataset_splits'].push(splitData);
    }
  }

  // Uses the same endpoint as while normally creating a challenge, but the form data will be different.
  createTemplateChallenge(){
    const FORM_DATA: FormData = new FormData();
    FORM_DATA.append('template_challenge_data', JSON.stringify(SELF.templateChallengeData));
    FORM_DATA.append('is_template_challenge', true);
    this.globalService.startLoader('Creating Challenge');
    this.challengeService.challengeCreate(
        this.hostTeam['id'],
        FORM_DATA,
      ).subscribe(
        data => {
          this.globalService.stopLoader();
          this.globalService.showToast('success', 'Successfuly sent to EvalAI admin for approval.');
          this.router.navigate([this.hostedChallengesRoute]);
        },
        err => {
          this.globalService.stopLoader();
          this.globalService.showToast('error', err.error.error);
        },
        () => {}
        );
  }

}