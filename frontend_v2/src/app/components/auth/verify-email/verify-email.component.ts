import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { AuthService } from '../../../services/auth.service';
import { GlobalService } from '../../../services/global.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-verify-email',
  templateUrl: './verify-email.component.html',
  styleUrls: ['./verify-email.component.scss'],
})
export class VerifyEmailComponent implements OnInit {
  /**
   * Email verification token local
   */
  token = '';

  /**
   * Is Email verified
   */
  email_verify_msg = '';

  /**
   * Login route path
   */
  loginRoute = '/auth/login';

  /**
   * Constructor.
   * @param authService  AuthService Injection.
   * @param globalService  GlobalService Injection.
   * @param route  ActivatedRoute Injection.
   */
  constructor(
    private route: ActivatedRoute,
    private globalService: GlobalService,
    private authService: AuthService
  ) {}

  /**
   * Component on initialized.
   */
  ngOnInit() {
    this.globalService.startLoader('Verifying Email');
    this.route.params.subscribe((params) => {
      if (params['token']) {
        this.token = params['token'];
        this.authService.verifyEmail(
          this.token,
          () => {
            this.email_verify_msg = 'Your email has been verified successfully';
            this.globalService.stopLoader();
          },
          () => {
            this.email_verify_msg = 'Something went wrong!! Please try again.';
            this.globalService.stopLoader();
          }
        );
      }
    });
  }
}
