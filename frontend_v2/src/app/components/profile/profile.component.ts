import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { ViewChildren, QueryList } from '@angular/core';
import { NGXLogger } from 'ngx-logger';

// import service
import { ApiService } from '../../services/api.service';
import { WindowService } from '../../services/window.service';
import { GlobalService } from '../../services/global.service';
import { EndpointsService } from '../../services/endpoints.service';
import { AuthService } from '../../services/auth.service';
import { InputComponent } from '../utility/input/input.component';

/**
 * Component Class
 */
@Component({
  selector: 'app-profile',
  templateUrl: './profile.component.html',
  styleUrls: ['./profile.component.scss'],
})
export class ProfileComponent implements OnInit {
  /**
   * User object
   */
  user: any;

  /**
   * Profile completion score
   */
  pcomp: any;

  /**
   * Auth token string
   */
  token = '';

  /**
   * Is modal visible
   */
  tokenModalButtonFlag = true;

  /**
   * Auth token Modal Button text
   */
  tokenModalButton = 'Show Token';

  /**
   * Modal display flag
   */
  isTokenModalVisible = false;

  /**
   * To call the API inside modal for updating the user details and password
   */
  apiCall: any;

  /**
   * Form components from 'formtoken'
   */
  @ViewChildren('formtoken')
  formTokenComponents: QueryList<InputComponent>;

  /**
   * Constructor.
   * @param route  ActivatedRoute Injection.
   * @param router  Router Injection.
   * @param globalService  GlobalService Injection.
   * @param authService  AuthService Injection.
   * @param apiService  ApiService Injection.
   * @param endpointsService  EndpointsService Injection.
   * @param windowService  WindowService Injection.
   */
  constructor(
    private apiService: ApiService,
    private authService: AuthService,
    private globalService: GlobalService,
    private router: Router,
    private endpointsService: EndpointsService,
    private windowService: WindowService,
    private logger: NGXLogger
  ) {}

  /**
   * Component on intialized.
   */
  ngOnInit() {
    if (!this.authService.isLoggedIn()) {
      this.globalService.storeData(this.globalService.redirectStorageKey, this.router.url);
      this.router.navigate(['/auth/login']);
    }
    this.authService.change.subscribe((details) => {
      this.user = details;
      this.setAccessToken();
      this.processUserDetails();
    });
  }

  /**
   * Set access token
   */
  setAccessToken() {
    const API_PATH = this.endpointsService.getAuthTokenURL();
    const SELF = this;

    SELF.apiService.getUrl(API_PATH).subscribe(
      (data) => {
        // Success Message in data.message
        this.token = data.token;
      },
      (err) => {
        SELF.globalService.handleApiError(err, true);
      },
      () => this.logger.info('GET-AUTH-TOKEN-FINISHED')
    );
  }

  /**
   * Refresh access token
   */
  refreshAccessToken() {
    const API_PATH = this.endpointsService.refreshAuthTokenURL();
    const SELF = this;

    SELF.apiService.getUrl(API_PATH).subscribe(
      (data) => {
        // Success Message in data.message
        this.token = data.token;
        SELF.globalService.showToast('success', 'Token generated successfully', 5);
      },
      (err) => {
        SELF.globalService.handleApiError(err, true);
      },
      () => this.logger.info('REFRESH-AUTH-TOKEN-FINISHED')
    );
  }

  /**
   * Process user details function.
   */
  processUserDetails() {
    let countLeft = 0;
    let count = 0;
    for (const i in this.user) {
      if (this.user.hasOwnProperty(i)) {
        if (this.user[i] === '' || this.user[i] === undefined || this.user[i] === null) {
          this.user[i] = '-';
          countLeft = countLeft + 1;
        }
        count = count + 1;
      }
    }
    const TEMP = ((countLeft / count) * 100).toString();
    this.pcomp = (100 - parseInt(TEMP, 10)).toString() + '%';
  }

  /**
   * Token Modal toggle function.
   */
  tokenModalButtonToggle() {
    this.tokenModalButtonFlag = !this.tokenModalButtonFlag;
    this.tokenModalButton = this.tokenModalButtonFlag ? 'Show Token' : 'Hide Token';
    const TOKEN_INPUT = this.globalService.formItemForLabel(this.formTokenComponents, 'token');
    TOKEN_INPUT.type = this.tokenModalButtonFlag ? 'password' : 'text';
  }

  /**
   * Displays a Modal to update user details
   */
  updateUserDetails() {
    const firstName = this.user['first_name'] === '-' ? '' : this.user['first_name'];
    const lastName = this.user['last_name'] === '-' ? '' : this.user['last_name'];
    const affiliation = this.user['affiliation'] === '-' ? '' : this.user['affiliation'];
    const googleScholarUrl = this.user['google_scholar_url'] === '-' ? '' : this.user['google_scholar_url'];
    const githubUrl = this.user['github_url'] === '-' ? '' : this.user['github_url'];
    const linkedinUrl = this.user['linkedin_url'] === '-' ? '' : this.user['linkedin_url'];
    const SELF = this;
    SELF.apiCall = (params) => {
      const BODY = JSON.stringify(params);
      SELF.apiService.putUrl(SELF.endpointsService.userDetailsURL(), BODY).subscribe(
        (data) => {
          // Success Message in data.message
          SELF.globalService.showToast('success', 'User details updated successfully', 5);
          SELF.authService.fetchUserDetails();
        },
        (err) => {
          SELF.globalService.handleApiError(err, true);
        },
        () => this.logger.info('USER-UPDATE-FINISHED')
      );
    };
    const PARAMS = {
      title: 'Update Profile',
      content: '',
      confirm: 'Submit',
      deny: 'Cancel',
      form: [
        {
          isRequired: true,
          label: 'first_name',
          name: 'update_first_name',
          placeholder: 'First Name',
          type: 'text',
          value: firstName,
        },
        {
          isRequired: true,
          label: 'last_name',
          name: 'update_last_name',
          placeholder: 'Last Name',
          type: 'text',
          value: lastName,
        },
        {
          isRequired: true,
          label: 'affiliation',
          name: 'update_affiliation',
          placeholder: 'Affiliated To',
          type: 'text',
          value: affiliation,
        },
        {
          isRequired: false,
          label: 'google_scholar_url',
          name: 'update_google_scholar_url',
          placeholder: 'Google Scholar Url',
          type: 'url',
          value: googleScholarUrl,
        },
        {
          isRequired: false,
          label: 'github_url',
          name: 'update_github_url',
          placeholder: 'GitHub Url',
          type: 'url',
          value: githubUrl,
        },
        {
          isRequired: false,
          label: 'linkedin_url',
          name: 'update_linkedin_url',
          placeholder: 'LinkedIn Url',
          type: 'url',
          value: linkedinUrl,
        },
      ],
      confirmCallback: SELF.apiCall,
    };
    SELF.globalService.showModal(PARAMS);
  }

  /**
   * Download Auth Token as a JSON file.
   */
  downloadToken() {
    this.isTokenModalVisible = false;
    this.windowService.downloadFile({ body: JSON.stringify({ token: this.token }) }, 'token.json', {
      type: 'text/json',
    });
  }

  /**
   * Copy auth token to clipboard.
   */
  copyToken() {
    this.windowService.copyToClipboard(this.token);
    this.globalService.showToast('success', 'Copied to clipboard', 5);
  }

  /**
   * Display modal to update password.
   */
  updatePassword() {
    const SELF = this;
    SELF.apiCall = (params) => {
      const BODY = JSON.stringify(params);
      SELF.apiService.postUrl(SELF.endpointsService.changePasswordURL(), BODY).subscribe(
        (data) => {
          // Success Message in data.message
          SELF.globalService.showToast('success', 'Password updated successfully', 5);
          SELF.authService.fetchUserDetails();
        },
        (err) => {
          if (err.status === 400 && err.error && err.error.old_password) {
            SELF.globalService.showToast('error', err.error.old_password[0], 5);
          } else if (err.status === 400 && err.error && err.error.new_password2) {
            SELF.globalService.showToast('error', err.error.new_password2[0], 5);
          } else {
            SELF.globalService.handleApiError(err, true);
          }
        },
        () => this.logger.info('PASSWORD-UPDATE-FINISHED')
      );
    };
    const PARAMS = {
      title: 'Change Password',
      content: '',
      isButtonDisabled: true,
      confirm: 'Submit',
      deny: 'Cancel',
      form: [
        {
          isRequired: true,
          label: 'old_password',
          name: 'old_password',
          placeholder: 'Old Password*',
          type: 'password',
        },
        {
          isRequired: true,
          label: 'new_password1',
          name: 'new_password1',
          placeholder: 'New Pasword*',
          type: 'password',
        },
        {
          isRequired: true,
          label: 'new_password2',
          name: 'new_password2',
          placeholder: 'New Password (Again)*',
          type: 'password',
        },
      ],
      confirmCallback: SELF.apiCall,
    };
    SELF.globalService.showModal(PARAMS);
  }
}
