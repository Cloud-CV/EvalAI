import { Component, OnInit, Inject } from '@angular/core';
import { DOCUMENT } from '@angular/common';
import { NGXLogger } from 'ngx-logger';

// import service
import { ChallengeService } from '../../../services/challenge.service';
import { ApiService } from '../../../services/api.service';
import { EndpointsService } from '../../../services/endpoints.service';
import { GlobalService } from '../../../services/global.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-challengeevaluation',
  templateUrl: './challengeevaluation.component.html',
  styleUrls: ['./challengeevaluation.component.scss'],
})
export class ChallengeevaluationComponent implements OnInit {
  /**
   * Challenge object
   */
  challenge: any;

  /**
   * Is challenge host
   */
  isChallengeHost = false;

  /**
   * Challenge evaluation DOM element
   */
  evaluationElement: any;

  /**
   * Challenge tnc DOM element
   */
  tncElement: any;

  /**
   * To call the API inside modal for editing the challenge evaluation
   * details, evaluation script and terms and conditions
   */
  apiCall: any;

  /**
   * Constructor.
   * @param document  window document Injection.
   * @param challengeService  ChallengeService Injection.
   */
  constructor(
    private challengeService: ChallengeService,
    @Inject(DOCUMENT) private document: Document,
    private endpointsService: EndpointsService,
    private apiService: ApiService,
    private globalService: GlobalService,
    private logger: NGXLogger
  ) {}

  /**
   * Component on init function.
   */
  ngOnInit() {
    this.evaluationElement = this.document.getElementById('challenge-evaluation');
    this.tncElement = this.document.getElementById('challenge-tnc');
    this.challengeService.currentChallenge.subscribe((challenge) => {
      this.challenge = challenge;
      this.updateView();
    });
    this.challengeService.isChallengeHost.subscribe((status) => {
      this.isChallengeHost = status;
    });
  }

  /**
   * Updating view function (Called after onInit)
   */
  updateView() {
    this.evaluationElement.innerHTML = this.challenge['evaluation_details'];
    this.tncElement.innerHTML = this.challenge['terms_and_conditions'];
  }

  /**
   * Edit evaluation criteria of the challenge
   */
  editEvaluationCriteria() {
    const SELF = this;
    SELF.apiCall = (params) => {
      const BODY = JSON.stringify(params);
      SELF.apiService
        .patchUrl(SELF.endpointsService.editChallengeDetailsURL(SELF.challenge.creator.id, SELF.challenge.id), BODY)
        .subscribe(
          (data) => {
            SELF.challenge.evaluation_details = data.evaluation_details;
            console.log(data);
            this.updateView();
            SELF.globalService.showToast('success', 'The evaluation details is successfully updated!', 5);
          },
          (err) => {
            SELF.globalService.handleApiError(err, true);
            SELF.globalService.showToast('error', err);
          },
          () => this.logger.info('EDIT-CHALLENGE-EVALUATION-DETAILS-FINISHED')
        );
    };

    /**
     * Parameters of the modal
     */
    const PARAMS = {
      title: 'Edit Evaluation Details',
      label: 'evaluation_details',
      isEditorRequired: true,
      editorContent: this.challenge.evaluation_details,
      confirm: 'Submit',
      deny: 'Cancel',
      confirmCallback: SELF.apiCall,
    };
    SELF.globalService.showModal(PARAMS);
  }

  /**
   * Edit terms and conditions of the challenge
   */
  editTermsAndConditions() {
    const SELF = this;
    SELF.apiCall = (params) => {
      const BODY = JSON.stringify(params);
      SELF.apiService
        .patchUrl(SELF.endpointsService.editChallengeDetailsURL(SELF.challenge.creator.id, SELF.challenge.id), BODY)
        .subscribe(
          (data) => {
            SELF.challenge.terms_and_conditions = data.terms_and_conditions;
            this.updateView();
            SELF.globalService.showToast('success', 'The terms and conditions are successfully updated!', 5);
          },
          (err) => {
            SELF.globalService.handleApiError(err, true);
            SELF.globalService.showToast('error', err);
          },
          () => this.logger.info('EDIT-TERMS-AND-CONDITIONS-FINISHED')
        );
    };

    /**
     * Parameters of the modal
     */
    const PARAMS = {
      title: 'Edit Terms And Conditions',
      label: 'terms_and_conditions',
      isEditorRequired: true,
      editorContent: this.challenge.terms_and_conditions,
      confirm: 'Submit',
      deny: 'Cancel',
      confirmCallback: SELF.apiCall,
    };
    SELF.globalService.showModal(PARAMS);
  }

  /**
   * Edit evaluation script of the challenge
   */
  editEvaluationScript() {
    const SELF = this;
    SELF.apiCall = (params) => {
      const FORM_DATA: FormData = new FormData();
      FORM_DATA.append('evaluation_script', params['evaluation_script']);
      SELF.apiService
        .patchFileUrl(
          SELF.endpointsService.editChallengeDetailsURL(SELF.challenge.creator.id, SELF.challenge.id),
          FORM_DATA
        )
        .subscribe(
          (data) => {
            SELF.globalService.showToast('success', 'The evaluation script is successfully updated!');
          },
          (err) => {
            SELF.globalService.showToast('error', err);
          },
          () => this.logger.info('EDIT-EVALUATION-SCRIPT-FINISHED')
        );
    };

    /**
     * Parameters of the modal
     */
    const PARAMS = {
      title: 'Edit Evaluation Script',
      confirm: 'Submit',
      deny: 'Cancel',
      form: [
        {
          name: 'evaluationScript',
          isRequired: true,
          label: 'evaluation_script',
          placeholder: '',
          type: 'file',
          value: '',
        },
      ],
      confirmCallback: SELF.apiCall,
    };
    SELF.globalService.showModal(PARAMS);
  }
}
