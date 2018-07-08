import { Injectable, Output, EventEmitter } from '@angular/core';

@Injectable()
export class AuthService {
  authState = {isLoggedIn: false};
  @Output() change: EventEmitter<Object> = new EventEmitter();

  constructor() { }

    authStateChange(state) {
      this.authState = state;
      this.change.emit(this.authState);
    }

    tryLogIn(params) {
      setTimeout(() => {
        const temp = {isLoggedIn: true, username: 'LoremIpsum'};
        this.authStateChange(temp);
      }, 1000);
    }
    logOut() {
      const temp = {isLoggedIn: false, username: 'LoremIpsum'};
      this.authStateChange(temp);
    }
    passwordStrength(password) {
      // Regular Expressions.
      const REGEX = new Array();
      REGEX.push('[A-Z]', '[a-z]', '[0-9]', '[$$!%*#?&]');

      let passed = 0;
      // Validate for each Regular Expression.
      for (let i = 0; i < REGEX.length; i++) {
        if (new RegExp(REGEX[i]).test(password)) {
          passed++;
        }
      }
      // Validate for length of Password.
      if (passed > 2 && password.length > 8) {
        passed++;
      }

      let color = '';
      let strength = '';
      if (passed === 1) {
        strength = 'Weak';
        color = 'red';
      } else if (passed === 2) {
        strength = 'Average';
        color = 'darkorange';
      } else if (passed === 3) {
        strength = 'Good';
        color = 'green';
      } else if (passed === 4) {
        strength = 'Strong';
        color = 'darkgreen';
      } else if (passed === 5) {
        strength = 'Very Strong';
        color = 'darkgreen';
      }
      return [strength, color];
    }

    // Get Login functionality
    get isLoggedIn() {
      // check for token present
      // TODO => change this token later to dynamic
      const token = true;

      if (token) {
          return true;
      } else {
          return false;
      }
    }
}
