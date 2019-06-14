import { Component, OnInit, Input, Inject } from '@angular/core';
import { DOCUMENT } from '@angular/common';
import { GlobalService } from '../../../services/global.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-input',
  templateUrl: './input.component.html',
  styleUrls: ['./input.component.scss']
})
export class InputComponent implements OnInit {

  /**
   * Placeholder string
   */
  @Input() placeholder: string;

  /**
   * Label string
   */
  @Input() label: string;

  /**
   * Type of input (text, password, email and file)
   */
  @Input() type: string;

  /**
   * Is it a required field
   */
  @Input() isRequired: boolean;

  /**
   * Dark / light
   */
  @Input() theme: string;

  /**
   * icon at the end of input field
   */
  @Input() icon: string;

  /**
   * Custom validate function
   */
  @Input() validate: Function;

  /**
   * Value of input field
   */
  @Input() value: string;

  /**
   * Is field read-only
   */
  @Input() readonly: boolean;

  /**
   * Is email flag
   */
  isEmail = false;

  /**
   * Is input field touched
   */
  isDirty = false;

  /**
   * Is field valid
   */
  isValid = false;

  /**
   * Is field empty
   */
  isEmpty = true;

  /**
   * Icon present flag
   */
  isIconPresent = false;

  /**
   * Is custom validate function provided
   */
  isValidateCustom = false;

  /**
   * read only flag
   */
  isReadonly = false;

  /**
   * file selected flag
   */
  fileSelected = null;

  /**
   * Input field message
   */
  message = 'Required field';

  /**
   * Input field message for required fields
   */
  requiredMessage = 'Required field';

  /**
   * Constructor.
   * @param document  Window document Injection.
   * @param globalService  GlobalService Injection.
   */
  constructor(@Inject(DOCUMENT) private document: Document, private globalService: GlobalService) {  }

  /**
   * Component on intialized
   */
  ngOnInit() {
    if (!this.type || this.type === 'email') {
      if (this.type === 'email') {
        this.isEmail = true;
      }
      this.type = 'text';
    }
    if (this.label === undefined) {
      this.label = 'Default Label';
    }
    if (this.isRequired === undefined) {
      this.isRequired = false;
    }
    if (this.theme === undefined) {
      this.theme = 'light';
    }
    if (this.icon !== undefined) {
      this.isIconPresent = true;
    }
    if (this.validate !== undefined) {
      this.isValidateCustom = true;
    }
    if (this.placeholder === undefined) {
      this.placeholder = this.label;
    }
    if (!this.value) {
      this.value = '';
    } else {
      this.isEmpty = false;
    }
    if (this.readonly) {
      this.isReadonly = true;
    }
  }

  /**
   * Perform validations on the input
   */
  validateInput(e) {
    this.isDirty = true;
    this.value = e;
    e === '' ? this.isEmpty = true : this.isEmpty = false;
    if (e === '' && this.isRequired) {
      this.isValid = false;
      this.isRequired ? this.message = this.requiredMessage : this.message = '';
    }
    if (this.isValidateCustom) {
       this.isValid = this.validate(e).is_valid;
       this.isValid ? this.message = '' : this.message = this.validate(e).message;
    } else if (this.isEmail) {
       this.isValid = this.globalService.validateEmail(e);
       this.isValid ? this.message = '' : this.message = 'Enter a valid email';
    } else if (this.type === 'text' || this.type === 'textarea') {
       this.isValid = this.globalService.validateText(e);
       this.isValid ? this.message = '' : this.message = 'Enter a valid text';
    } else if (this.type === 'password') {
       this.isValid = this.globalService.validatePassword(e);
       this.isValid ? this.message = '' : this.message = 'Password minimum 8 characters';
    }
  }

  /**
   * Handle file input (like validateInput, but for files).
   */
  handleFileInput(f) {
    if (f && f.length >= 1) {
      this.fileSelected = f.item(0);
      this.placeholder = this.fileSelected['name'];
      this.isValid = true;
      this.isValid ? this.message = '' : this.message = this.requiredMessage;
    }
  }

  /**
   * Trigger click on a DOM element.
   * @param id  id of DOM element to be clicked
   */
  transferClick(id) {
    this.document.getElementById(id).click();
  }

  toggleErrorMessage () {
    if (((this.isRequired && this.isEmpty) || (!this.isValid && !this.isEmpty)) && this.isDirty) {
      return false;
    } else {
      return true;
    }
  }
}
