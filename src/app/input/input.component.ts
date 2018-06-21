import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'app-input',
  templateUrl: './input.component.html',
  styleUrls: ['./input.component.scss']
})
export class InputComponent implements OnInit {
  @Input() label: string;
  @Input() type: string;
  @Input() isRequired: boolean;
  @Input() theme: string;
  @Input() icon: string;
  @Input() validate: Function;
  isEmail = false;
  isDirty = false;
  isValid = false;
  isEmpty = true;
  isIconPresent = false;
  isValidateCustom = false;
  value = '';
  message = 'Required field';
  requiredMessage = 'Required field';
  constructor() {  }

  ngOnInit() {
    if (!this.type || this.type === 'email') {
      if (this.type === 'email') {
        this.isEmail = true;
      }
      this.type = 'text';
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
  }

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
       this.isValid = this.validateEmail(e);
       this.isValid ? this.message = '' : this.message = 'Enter a valid email';
    } else if (this.type === 'text') {
       this.isValid = this.validateText(e);
       this.isValid ? this.message = '' : this.message = 'Enter a valid text';
    } else if (this.type === 'password') {
       this.isValid = this.validatePassword(e);
       this.isValid ? this.message = '' : this.message = 'Password minimum 8 characters';
    }
  }

  validateEmail(email) {
    const RE = new RegExp (['^(([^<>()[\\]\\\.,;:\\s@\"]+(\\.[^<>()\\[\\]\\\.,;:\\s@\"]+)*)',
                        '|(".+"))@((\\[[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.',
                        '[0-9]{1,3}\])|(([a-zA-Z\\-0-9]+\\.)+',
                        '[a-zA-Z]{2,}))$'].join(''));
    return RE.test(email);
  }
  validateText(text) {
    if (text.length >= 2) {
      return true;
    }
    return false;
  }
  validatePassword(password) {
    if (password.length >= 8) {
      return true;
    }
    return false;
  }
}
