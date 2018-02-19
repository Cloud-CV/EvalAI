import { Injectable } from '@angular/core';

@Injectable()
export class AuthService {

  constructor() { }

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
