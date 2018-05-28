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
