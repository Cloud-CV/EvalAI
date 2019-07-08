import { Component, OnInit, Input } from '@angular/core';
import { ViewChildren, QueryList, AfterViewInit } from '@angular/core';
import { GlobalService } from '../../../services/global.service';
import { InputComponent } from '../input/input.component';
import { ChallengeService } from '../../../services/challenge.service';

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
   * Modal body
   */
  content = '';

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
   * delete challenge button disable
   */
  isDisabled = true;

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
  constructor(private globalService: GlobalService, private challengeService: ChallengeService) { }

  /**
   * Component on intialized.
   */
  ngOnInit() {
    if (this.params) {
      if (this.params['title']) {
        this.title = this.params['title'];
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
    if (this.isEditorRequired) {
      this.isDisabled = false;
    }

    this.challengeService.currentChallenge.subscribe(challenge => this.challenge = challenge);
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
    const content_text = document.createElement('div');
    content_text.innerHTML = this.editorContent;
    const actual_text = content_text.textContent || content_text.innerText || '';
    if (actual_text.trim() === '') {
      this.denyCallback();
      this.isInputMessage = true;
      this.editorValidationMessage = 'Challenge description cannot be empty!';
    } else {
      self.globalService.hideModal();
      let PARAMS = self.globalService.formFields(self.formComponents);
      if (this.isEditorRequired) {
        PARAMS = {
          description: this.editorContent
        };
      }
      self.confirmCallback(PARAMS);
    }
  }

  /**
   * Modal Denied.
   */
  denied() {
    this.globalService.hideModal();
    this.denyCallback();
  }

  validateModalInput(e) {
    if (e.target.name === 'challegenDeleteInput') {
      if (e.target.value === this.challenge.title) {
        this.isDisabled = false;
      } else {
        this.isDisabled = true;
      }
    } else if (e.target.name === 'editChallengeTitle') {
      if (e.target.value !== this.challenge.title && e.target.value.length > 1) {
        this.isDisabled = false;
      } else {
        this.isDisabled = true;
      }
    }
  }

}
