import { ViewChildren, QueryList, Component, Input, OnInit } from '@angular/core';
import { GlobalService } from '../../../../services/global.service';
import { InputComponent } from '../../../utility/input/input.component';
import { NGXLogger } from 'ngx-logger';

import { EndpointsService } from '../../../../services/endpoints.service';
import { ApiService } from '../../../../services/api.service';
import { ChallengeService } from '../../../../services/challenge.service';


@Component({
  selector: 'app-editphasemodal',
  templateUrl: './editphasemodal.component.html',
  styleUrls: ['./editphasemodal.component.scss'],
})
export class EditphasemodalComponent implements OnInit {
  /**
   * Input parameters object
   */
  @Input() params: any;

  /**
   * To call the API inside modal for editing the challenge details
   */
  apiCall: any;

  /**
   * Challenge object
   */
  challenge: any;
   
  /**
   * Challenge object
   */
  phase: any;

  /**
   * Modal title
   */
  title = 'Edit Challenge Phase Details';

  /**
   * Label for the editor field i.e. challenge phase description
   */
  label = '';

  /**
   * Challenge phase name
   */
  name = '';
  
  /**
   * Challenge phase allowed submission file types
   */
  allowedSubmissionFileTypes = '';

  /**
   * Challenge phase description
   */
  description = '';

  /**
   * Challenge phase start date
   */
  startDate = '';

  /**
   * Challenge phase end date
   */
  endDate = '';

  /**
   * Challenge phase max submissions per day
   */
  maxSubmissionsPerDay: number;

  /**
   * Challenge phase max submissions per month
   */
  maxSubmissionsPerMonth: number;

  /**
   * Challenge phase max submissions
   */
  maxSubmissions: number;

  /**
   * Challenge phase max concurrent submissions allowed
   */
  maxConcurrentSubmissionsAllowed: number;

  /**
   * If editor error message
   */
  isEditorFieldMessage = false;

  /**
   * If per day maximum submission error message
   */
  isPerDaySubmissionFieldMessage = false;

  /**
   * If per month maximum submission error message
   */
  isPerMonthSubmissionFieldMessage = false;

  /**
   * Editor validation message
   */
  editorValidationMessage = '';

  /**
   * per day submission validation message
   */
  perDaySubmisionValidationMessage = '';

  /**
   * Editor validation message
   */
  PerMonthSubmissionValidationMessage = '';

  /**
   * Modal accept button
   */
  confirm = 'Submit';

  /**
   * Modal deny button
   */
  deny = 'Cancel';

  /**
   * Today's date time
   */
  todayDateTime: Date;

  /**
   * delete challenge button disable
   */
  isDisabled = false;

  /**
   * Is edit phase details
   */
  editPhaseDetails = true;

  /**
   * publish challenge state and it's icon
   */
  phaseVisibility = {
    state: 'Private',
    icon: 'fa fa-eye-slash red-text',
  };

  /**
   * Quill editor style
   */
  quillEditorStyle = {
    height: '320px',
    width: '712px',
  };

  /**
   * Modal form items
   */
  @ViewChildren('formmodal')
  formComponents: QueryList<InputComponent>;

  /**
   * Modal confirmed callback
   */
  confirmCallback = (params) => {};

  /**
   * Modal denied callback
   */
  denyCallback = () => {};

  /**
   * Constructor.
   * @param globalService  GlobalService Injection.
   */
  constructor(
    private globalService: GlobalService,
    private apiService: ApiService,
    private endpointsService: EndpointsService,
    private challengeService: ChallengeService,
    private logger: NGXLogger
    ) {}

  ngOnInit() {
    if (this.params) {
      if (this.params['title']) {
        this.title = this.params['title'];
      }
      if (this.params['challenge']) {
        this.challenge = this.params['challenge'];
      }
      if (this.params['phase']) {
        this.phase = this.params['phase'];
      }
      if (this.params['isPublic']) {
        this.phaseVisibility.state = 'Public';
        this.phaseVisibility.icon = 'fa fa-eye green-text';
      }
      if (this.params['label']) {
        this.label = this.params['label'];
      }
      if (this.params['name']) {
        this.name = this.params['name'];
      }
      if (this.params['description']) {
        this.description = this.params['description'];
      }
      if (this.params['startDate']) {
        this.startDate = this.params['startDate'];
      }
      if (this.params['endDate']) {
        this.endDate = this.params['endDate'];
      }
      if (this.params['maxSubmissionsPerDay']) {
        this.maxSubmissionsPerDay = this.params['maxSubmissionsPerDay'];
      }
      if (this.params['maxSubmissionsPerMonth']) {
        this.maxSubmissionsPerMonth = this.params['maxSubmissionsPerMonth'];
      }
      if (this.params['maxSubmissions']) {
        this.maxSubmissions = this.params['maxSubmissions'];
      }
      if (this.params['maxConcurrentSubmissionsAllowed']) {
        this.maxConcurrentSubmissionsAllowed = this.params['maxConcurrentSubmissionsAllowed'];
      }
      if (this.params['allowedSubmissionFileTypes']) {
        this.allowedSubmissionFileTypes = this.params['allowedSubmissionFileTypes'];
      }
      if (this.params['confirm']) {
        this.confirm = this.params['confirm'];
      }
      if (this.params['deny']) {
        this.deny = this.params['deny'];
      }
      if (this.params['confirmCallback']) {
        this.confirmCallback = this.params['confirmCallback'];
      }
      if (this.params['denyCallback']) {
        this.denyCallback = this.params['denyCallback'];
      }
    }
    this.todayDateTime = new Date();
  }

  /**
   * Phase Visibility click function
   */
  togglePhaseVisibility() {
    const SELF = this;
    let togglePhaseVisibilityState, isPublic;
    if (this.phaseVisibility.state === 'Public') {
      togglePhaseVisibilityState = 'private';
      isPublic = false;
    } else {
      togglePhaseVisibilityState = 'public';
      isPublic = true;
    }
    SELF.apiCall = () => {
      const BODY: FormData = new FormData();
      BODY.append("is_public", isPublic);
      SELF.apiService
      .patchFileUrl(
        SELF.endpointsService.updateChallengePhaseDetailsURL(SELF.params['challenge'], SELF.params['phase']),
        BODY
      )
        .subscribe(
          (data) => {
            SELF.challengeService.fetchPhases(SELF.params['challenge']);
            SELF.denied();
            if (isPublic) {
              this.phaseVisibility.state = 'Public';
              this.phaseVisibility.icon = 'fa fa-eye green-text';
            } else {
              this.phaseVisibility.state = 'Private';
              this.phaseVisibility.icon = 'fa fa-eye-slash red-text';
            }
            SELF.globalService.showToast(
              'success',
              'The phase was successfully made ' + togglePhaseVisibilityState,
              5
            );
          },
          (err) => {
            SELF.globalService.handleApiError(err, true);
            SELF.globalService.showToast('error', err);
          },
          () => this.logger.info('PHASE-VISIBILITY-UPDATE-FINISHED')
        );
    };

    const PARAMS = {
      title: 'Make this phase ' + togglePhaseVisibilityState + '?',
      content: '',
      confirm: "Yes, I'm sure",
      deny: 'No',
      confirmCallback: SELF.apiCall,
    };
    SELF.globalService.showConfirm(PARAMS);
  }

  /**
   * Form Validate function.
   */
  formValidate() {
    this.formComponents.map((val) => {
      if (val.label === 'max_submissions_per_day') {
        this.maxSubmissionsPerDay = parseInt(val.value, 10);
      }
      if (val.label === 'max_submissions_per_month') {
        this.maxSubmissionsPerMonth = parseInt(val.value, 10);
      }
      if (val.label === 'max_submissions') {
        this.maxSubmissions = parseInt(val.value, 10);
      }
    });
    if (this.formComponents.length > 0) {
      this.globalService.formValidate(this.formComponents, this.confirmed, this);
    } else {
      this.confirmed(this);
    }
  }

  /**
   * Modal Confirmed.
   */
  confirmed(self) {
    if (self.description === '') {
      self.denyCallback();
      self.isEditorFieldMessage = true;
      self.editorValidationMessage = 'This field cannot be empty!';
      return;
    }
    if (self.maxSubmissionsPerDay > self.maxSubmissionsPerMonth) {
      self.denyCallback();
      self.isPerDaySubmissionFieldMessage = true;
      self.perDaySubmisionValidationMessage =
        'Max number of per day submission cannot be greater than max number of per month submissions';
      return;
    }
    if (self.maxSubmissionsPerMonth > self.maxSubmissions) {
      self.denyCallback();
      self.isPerMonthSubmissionFieldMessage = true;
      self.PerMonthSubmissionValidationMessage =
        'Max number of per month submissions cannot be greater than max total submissions';
      return;
    }
    const PARAMS = self.globalService.formFields(self.formComponents);
    PARAMS[self.label] = self.description;
    self.globalService.hideEditPhaseModal();
    self.confirmCallback(PARAMS);
  }

  /**
   * Modal Denied.
   */
  denied() {
    this.globalService.hideEditPhaseModal();
    this.denyCallback();
  }
}
