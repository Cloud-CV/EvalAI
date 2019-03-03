import { Component, OnInit, ViewChildren, QueryList } from '@angular/core';
import { AuthService } from '../../services/auth.service';
import { ApiService } from '../../services/api.service';
import { GlobalService } from '../../services/global.service';
import { ChallengeService } from '../../services/challenge.service';
import { Router, ActivatedRoute } from '@angular/router';

/**
 * Component Class
 */
@Component({
  selector: 'app-challenge-create',
  templateUrl: './challenge-create.component.html',
  styleUrls: ['./challenge-create.component.scss']
})
export class ChallengeCreateComponent implements OnInit {

  /**
   * Auth Service public instance
   */
  authServicePublic = null;

  /**
   * Is user logged in
   */
  isLoggedIn = false;

  /**
   * Router public instance
   */
  routerPublic = null;

  /**
   * Form fields name
   */
  submitForm = 'formcreate';

  /**
   * Selected Host team object
   */
  hostTeam: any = null;

  /**
   * Component Class
   */
  @ViewChildren('formcreate')
  components: QueryList<ChallengeCreateComponent>;

  /**
   * Constructor.
   * @param route  ActivatedRoute Injection.
   * @param router  Router Injection.
   * @param authService  AuthService Injection.
   * @param globalService  GlobalService Injection.
   * @param apiService  ApiService Injection.
   * @param challengeService  ChallengeService Injection.
   */
  constructor(private authService: AuthService, private router: Router, private route: ActivatedRoute,
              private challengeService: ChallengeService, private globalService: GlobalService, private apiService: ApiService) { }

  /**
   * Component on initialized.
   */
  ngOnInit() {
    if (this.authService.isLoggedIn()) {
      this.isLoggedIn = true;
    }
    this.authServicePublic = this.authService;
    this.routerPublic = this.router;
    this.challengeService.currentHostTeam.subscribe((hostTeam) => {
      this.hostTeam = hostTeam;
      if (!hostTeam) {
        setTimeout(() => {
          this.globalService.showToast('info', 'Please select a host team');
        }, 1000);
        this.router.navigate(['/teams/hosts']);
      }
    });
  }

  /**
   * Form Validate function.
   */
  formValidate(formname) {
    this.globalService.formValidate(this.components, this.formSubmit, this);
  }

  /**
   * Form Submit function (Called after validation).
   */
  formSubmit(self) {
    const FORM_DATA: FormData = new FormData();
    FORM_DATA.append('status', 'submitting');
    FORM_DATA.append('zip_configuration', self.globalService.formItemForLabel(self.components, 'zip_configuration').fileSelected);
    const SUCCESS_CALLBACK = () => {
      self.router.navigate(['/challenges/me']);
    };
    self.challengeService.challengeCreate(
      self.hostTeam['id'],
      FORM_DATA,
      SUCCESS_CALLBACK
    );
  }

}
