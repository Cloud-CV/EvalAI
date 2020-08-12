import { Component, OnInit } from '@angular/core';

//  import service
import { ApiService } from '../../services/api.service';
import { GlobalService } from '../../services/global.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-permission-denied',
  templateUrl: './permission-denied.component.html',
  styleUrls: ['./permission-denied.component.scss'],
})
export class PermissionDeniedComponent implements OnInit {
  constructor(private apiService: ApiService, private globalService: GlobalService, private authService: AuthService) {}

  sendMail = false;

  ngOnInit() {}

  requestLink() {
    const API_PATH = 'accounts/user/resend_email_verification/';
    const SELF = this;
    const token = this.authService.getUser['token'];
    const EMAIL_BODY = JSON.stringify({
      key: token,
    });
    SELF.apiService.postUrl(API_PATH, EMAIL_BODY).subscribe(
      (data) => {
        SELF.sendMail = true;
        SELF.globalService.showToast('success', 'The verification link was sent again.', 5);
      },
      (err) => {
        SELF.globalService.stopLoader();
        const message = err.error.detail;
        const time = Math.floor(message.match(/\d+/g)[0] / 60);
        if (err.status === 429) {
          SELF.globalService.showToast(
            'error',
            'Request limit exceeded. Please wait for ' + time + ' minutes and try again.',
            5
          );
        } else {
          SELF.globalService.handleApiError(err);
        }
      },
      () => {}
    );
  }
}
