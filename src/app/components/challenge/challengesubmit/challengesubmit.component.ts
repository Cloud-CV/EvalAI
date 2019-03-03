import { Component, OnInit, QueryList, ViewChildren } from '@angular/core';
import { AuthService } from '../../../services/auth.service';
import { ApiService } from '../../../services/api.service';
import { GlobalService } from '../../../services/global.service';
import { ChallengeService } from '../../../services/challenge.service';
import { Router, ActivatedRoute } from '@angular/router';
import { EndpointsService } from '../../../services/endpoints.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-challengesubmit',
  templateUrl: './challengesubmit.component.html',
  styleUrls: ['./challengesubmit.component.scss']
})
export class ChallengesubmitComponent implements OnInit {

  /**
   * Is user logged in
   */
  isLoggedIn = false;

  /**
   * Challenge object
   */
  challenge: any;

  /**
   * Router public instance
   */
  routerPublic: any;

  /**
   * Is user a participant
   */
  isParticipated: any;

  /**
   * Is challenge currently active
   */
  isActive: any;

  /**
   * Guidelines text
   */
  submissionGuidelines = '';

  /**
   * Form fields name
   */
  submitForm = 'formsubmit';

  /**
   * Challenge phases list
   */
  phases = [];

  /**
   * Filtered challenge phases
   */
  filteredPhases = [];

  /**
   * Selected phase object
   */
  selectedPhase = null;

  /**
   * Submissions remaining for the selected phase
   */
  selectedPhaseSubmissions = {
    remaining_submissions_today_count: 0,
    remaining_submissions: 0
  };

  /**
   * Component Class
   */
  @ViewChildren('formsubmit')
  components: QueryList<ChallengesubmitComponent>;

  /**
   * Constructor.
   * @param route  ActivatedRoute Injection.
   * @param router  Router Injection.
   * @param authService  AuthService Injection.
   * @param globalService  GlobalService Injection.
   * @param apiService  ApiService Injection.
   * @param challengeService  ChallengeService Injection.
   */
  constructor(private authService: AuthService, private router: Router, private route: ActivatedRoute,
              private challengeService: ChallengeService, private globalService: GlobalService, private apiService: ApiService,
              private endpointsService: EndpointsService) { }

  /**
   * Component on intialization.
   */
  ngOnInit() {
    if (this.authService.isLoggedIn()) {
      this.isLoggedIn = true;
    }
    this.routerPublic = this.router;
    this.challengeService.currentChallenge.subscribe(challenge => {
      this.challenge = challenge;
      this.isActive = this.challenge['is_active'];
      this.submissionGuidelines = this.challenge['submission_guidelines'];
    });
    this.challengeService.currentParticipationStatus.subscribe(status => {
      this.isParticipated = status;
      if (!status) {
        console.log('navigating to /participate');
        this.router.navigate(['../participate'], {relativeTo: this.route});
      }
    });
    this.challengeService.currentPhases.subscribe(
      phases => {
        this.phases = phases;
        this.filteredPhases = this.phases.filter(phase => phase['is_active'] === true);
    });
  }

  /**
   * Fetch remaining submissions for a challenge phase.
   * @param challenge  challenge id
   * @param phase  phase id
   */
  fetchRemainingSubmissions(challenge, phase) {
    const API_PATH = this.endpointsService.challengeSubmissionsRemainingURL(challenge, phase);
    const SELF = this;
    this.apiService.getUrl(API_PATH).subscribe(
      data => {
        if (data['remaining_submissions']) {
          SELF.selectedPhaseSubmissions = data;
        } else if (data['message']) {
          SELF.selectedPhaseSubmissions['remaining_submissions_today_count'] = 0;
          SELF.globalService.showToast('info', data['message']);
        }
      },
      err => {
        SELF.globalService.handleApiError(err);
      },
      () => {
        console.log('Remaining submissions fetched for challenge-phase', challenge, phase);
      }
    );
  }

  /**
   * Called when a phase is selected (from child components)
   */
  phaseSelected() {
    const SELF = this;
    return (phase) => {
      SELF.selectedPhase = phase;
      if (SELF.challenge['id'] && phase['id']) {
        SELF.fetchRemainingSubmissions(SELF.challenge['id'], phase['id']);
      }
    };
  }

  /**
   * Form validate function
   * @param formname  name of the form fields (#)
   */
  formValidate(formname) {
    if (this.selectedPhaseSubmissions['remaining_submissions_today_count']) {
      this.globalService.formValidate(this.components, this.formSubmit, this);
    } else {
      this.globalService.showToast('info', 'You have exhausted today\'s submission limit');
    }
  }

  /**
   * Form submit function
   * @param self  context value of this
   */
  formSubmit(self) {
    const FORM_DATA: FormData = new FormData();
    FORM_DATA.append('status', 'submitting');
    FORM_DATA.append('input_file', self.globalService.formItemForLabel(self.components, 'input_file').fileSelected);
    FORM_DATA.append('method_name', self.globalService.formValueForLabel(self.components, 'method_name'));
    FORM_DATA.append('method_description', self.globalService.formValueForLabel(self.components, 'method_description'));
    FORM_DATA.append('project_url', self.globalService.formValueForLabel(self.components, 'project_url'));
    FORM_DATA.append('publication_url', self.globalService.formValueForLabel(self.components, 'publication_url'));
    self.challengeService.challengeSubmission(
      self.challenge['id'],
      self.selectedPhase['id'],
      FORM_DATA
    );
  }
}
