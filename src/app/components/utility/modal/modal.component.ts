import { Component, OnInit, Input } from '@angular/core';
import { ViewChildren, QueryList, AfterViewInit } from '@angular/core';
import { GlobalService } from '../../../services/global.service';
import { InputComponent } from '../input/input.component';
import { ChallengeService } from '../../../services/challenge.service';
import { AuthService } from '../../../services/auth.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-modal',
  templateUrl: './modal.component.html',
  styleUrls: ['./modal.component.scss']
})
export class ModalComponent implements OnInit {

  /**
   * Input parameters object
   */
  @Input() params: any;

  /**
   * Modal title
   */
  title = 'Are you sure ?';

  /**
   * Modal field label
   */
  label = '';

  /**
   * Modal body
   */
  content = '';

  /**
   * Modal name
   */
  isButtonDisabled: boolean;

  /**
   * If rich text editor required
   */
  isEditorRequired = false;

  /**
   * Modal edit content
   */
  editorContent = '';

  /**
   * If editor error message
   */
  isInputMessage = false;

  /**
   * Editor validation message
   */
  editorValidationMessage = '';

  /**
   * Modal accept button
   */
  confirm = 'Yes';

  /**
   * Modal deny button
   */
  deny = 'Cancel';

  /**
   * Modal form items list
   */
  form = [];

  /**
   * challenge object
   */
  challenge: any;

  /**
   * User object
   */
  user: any;

  /**
   * Old password
   */
  oldPassword = '';

  /**
   * New password
   */
  newPassword = '';

  /**
   * Re-type new password
   */
  retype_newPassword = '';

  /**
   * delete challenge button disable
   */
  isDisabled = true;

  /**
   * Input field message
   */
  inputErrorMessage = '';

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
  constructor(private globalService: GlobalService, private challengeService: ChallengeService,
              private authService: AuthService) { }

  /**
   * Component on intialized.
   */
  ngOnInit() {
    if (this.params) {
      if (this.params['title']) {
        this.title = this.params['title'];
      }
      if (this.params['label']) {
        this.label = this.params['label'];
      }
      if (this.params['isButtonDisabled']) {
        this.isButtonDisabled = this.params['isButtonDisabled'];
      }
      if (this.params['isEditorRequired']) {
        this.isEditorRequired = this.params['isEditorRequired'];
      }
      if (this.params['editorContent']) {
        this.editorContent = this.params['editorContent'];
      }
      if (this.params['content']) {
        this.content = this.params['content'];
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
      if (this.params['form'] && this.params['form'].length > 0) {
        this.form = this.params['form'];
      }
    }

    this.authService.change.subscribe((details) => {
      this.user = details;
    });

    if (this.isEditorRequired || this.isButtonDisabled) {
      this.isDisabled = false;
    }
    this.challengeService.currentChallenge.subscribe(challenge => this.challenge = challenge);
  }

  /**
   * Form Validate function.
   */
  formValidate() {
    if (this.formComponents.length > 0) {
      console.log(this.formComponents);
      if (this.title === 'Update Profile') {
        this.confirmed(this);
      } else {
        this.globalService.formValidate(this.formComponents, this.confirmed, this);
      }
    } else {
      this.confirmed(this);
    }
  }

  /**
   * Modal Confirmed.
   */
  confirmed(self) {
    let PARAMS = {};
    if (self.isEditorRequired) {
      const content_text = document.createElement('div');
      content_text.innerHTML = this.editorContent;
      const actual_text = content_text.textContent || content_text.innerText || '';
      if (actual_text.trim() === '') {
        self.denyCallback();
        self.isInputMessage = true;
        self.editorValidationMessage = 'This field cannot be empty!';
        return;
      }
      PARAMS[self.label] = self.editorContent;
    } else {
      PARAMS = self.globalService.formFields(self.formComponents);
    }
    self.globalService.hideModal();
    self.confirmCallback(PARAMS);
  }

  /**
   * Modal Denied.
   */
  denied() {
    this.globalService.hideModal();
    this.denyCallback();
  }

  validateModalInput(e) {
    this.inputErrorMessage = '';
    if (e.target.name === 'challegenDeleteInput') {
      this.isDisabled = e.target.value !== this.challenge.title;
    } else if (e.target.name === 'editChallengeTitle') {
      this.isDisabled = e.target.value === this.challenge.title;
    } else if (e.target.name === 'update_first_name') {
      this.isDisabled = e.target.value === this.user.first_name;
    } else if (e.target.name === 'update_last_name') {
      this.isDisabled = e.target.value === this.user.last_name;
    } else if (e.target.name === 'update_affiliation') {
      this.isDisabled = e.target.value === this.user.affiliation;
    } else if (e.target.name === 'old_password') {
      this.oldPassword = e.target.value;
    } else if (e.target.name === 'new_password1') {
      this.newPassword = e.target.value;
      if (e.target.value === this.oldPassword) {
        this.inputErrorMessage = 'Old password cannot be same as New Password';
      }
    } else if (e.target.name === 'new_password2') {
      this.retype_newPassword = e.target.value;
      if (e.target.value !== this.newPassword) {
        this.inputErrorMessage = 'Password do not match';
      }
    }
  }

  validateFileInput(e) {
    this.isDisabled = e.target.value === '';
  }
}
