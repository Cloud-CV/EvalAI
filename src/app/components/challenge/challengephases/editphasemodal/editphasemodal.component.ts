import { ViewChildren, QueryList, Component, Input, OnInit } from '@angular/core';
import { GlobalService } from '../../../../services/global.service';
import { InputComponent } from '../../../utility/input/input.component';

@Component({
  selector: 'app-editphasemodal',
  templateUrl: './editphasemodal.component.html',
  styleUrls: ['./editphasemodal.component.scss']
})
export class EditphasemodalComponent implements OnInit {

  /**
   * Input parameters object
   */
  @Input() params: any;

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
   * If editor error message
   */
  isEditorFieldMessage = false;

  /**
   * Editor validation message
   */
  editorValidationMessage = '';

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
  constructor(private globalService: GlobalService) { }

  ngOnInit() {
    if (this.params) {
      if (this.params['title']) {
        this.title = this.params['title'];
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
   * Form Validate function.
   */
  formValidate() {
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
