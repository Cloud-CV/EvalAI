import { Component, OnInit, ViewChildren, QueryList, Inject } from '@angular/core';
import { AuthService } from '../../services/auth.service';
import { ApiService } from '../../services/api.service';
import { GlobalService } from '../../services/global.service';
import { ChallengeService } from '../../services/challenge.service';
import { Router, ActivatedRoute } from '@angular/router';
import { DOCUMENT } from '@angular/common';

/**
 * Component Class
 */
@Component({
  selector: 'app-challenge-create',
  templateUrl: './challenge-create.component.html',
  styleUrls: ['./challenge-create.component.scss'],
})
export class ChallengeCreateComponent implements OnInit {
  isFormError = false;
  isSyntaxErrorInYamlFile = false;
  ChallengeCreateForm = {
    input_file: null,
    file_path: null,
  };
  syntaxErrorInYamlFile = {};

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
   * Selected Host team object
   */
  hostTeam: any = null;

  /**
   * Route for hosted challenges
   */
  hostedChallengesRoute = '/challenges/me';

  /**
   * Route path for host teams
   */
  hostTeamsRoute = '/teams/hosts';

  /**
   * Constructor.
   * @param route  ActivatedRoute Injection.
   * @param router  Router Injection.
   * @param authService  AuthService Injection.
   * @param document
   * @param globalService  GlobalService Injection.
   * @param apiService  ApiService Injection.
   * @param challengeService  ChallengeService Injection.
   */
  constructor(
    public authService: AuthService,
    private router: Router,
    private route: ActivatedRoute,
    private challengeService: ChallengeService,
    @Inject(DOCUMENT) private document,
    private globalService: GlobalService,
    private apiService: ApiService
  ) {}

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
        this.router.navigate([this.hostTeamsRoute]);
      }
    });
  }

  challengeCreate() {
    if (this.ChallengeCreateForm['input_file'] !== null) {
      const FORM_DATA: FormData = new FormData();
      FORM_DATA.append('status', 'submitting');
      FORM_DATA.append('zip_configuration', this.ChallengeCreateForm['input_file']);
      this.globalService.startLoader('Creating Challenge');
      this.challengeService.challengeCreate(this.hostTeam['id'], FORM_DATA).subscribe(
        (data) => {
          this.globalService.stopLoader();
          this.globalService.showToast('success', 'Successfuly sent to EvalAI admin for approval.');
          this.router.navigate([this.hostedChallengesRoute]);
        },
        (err) => {
          this.globalService.stopLoader();
          this.globalService.showToast('error', err.error.error);
          this.isSyntaxErrorInYamlFile = true;
          this.syntaxErrorInYamlFile = err.error.error;
        },
        () => {}
      );
    } else {
      this.isFormError = true;
      this.globalService.showToast('error', 'Please Upload File');
    }
  }

  handleUpload(event) {
    const files = event.target.files;

    if (files.length >= 1) {
      this.isFormError = false;
      this.ChallengeCreateForm['input_file'] = event.target.files[0];
      this.ChallengeCreateForm['file_path'] = event.target.files[0]['name'];
      this.document.getElementsByClassName('file-path')[0].value = event.target.files[0]['name'];
    } else {
      this.isFormError = true;
    }
  }
}
