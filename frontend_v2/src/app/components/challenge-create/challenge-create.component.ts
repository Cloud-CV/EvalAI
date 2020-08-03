import {Component, OnInit, ViewChildren, QueryList, Inject} from '@angular/core';
import { AuthService } from '../../services/auth.service';
import { ApiService } from '../../services/api.service';
import { GlobalService } from '../../services/global.service';
import { ChallengeService } from '../../services/challenge.service';
import { Router, ActivatedRoute } from '@angular/router';
import {DOCUMENT} from '@angular/common';

/**
 * Component Class
 */
@Component({
  selector: 'app-challenge-create',
  templateUrl: './challenge-create.component.html',
  styleUrls: ['./challenge-create.component.scss']
})
export class ChallengeCreateComponent implements OnInit {

  isFormError = false;
  isSyntaxErrorInYamlFile = false;
  ChallengeCreateForm = {
    input_file: null,
    file_path: null
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

  challengeTemplates = null;

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
  constructor(public authService: AuthService, private router: Router, private route: ActivatedRoute,
              private challengeService: ChallengeService, @Inject(DOCUMENT) private document,
              private globalService: GlobalService, private apiService: ApiService) { }

  /**
   * Component on initialized.
   */
  ngOnInit() {
    if (this.authService.isLoggedIn()) {
      this.isLoggedIn = true;
    }
    this.authServicePublic = this.authService;
    this.routerPublic = this.router;
    this.fetchChallengeTemplates();
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
      this.challengeService.challengeCreate(
        this.hostTeam['id'],
        FORM_DATA,
      ).subscribe(
        data => {
          this.globalService.stopLoader();
          this.globalService.showToast('success', 'Successfuly sent to EvalAI admin for approval.');
          this.router.navigate([this.hostedChallengesRoute]);
        },
        err => {
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

  // This method should run on loading the challenge create page, and fetches all templates from backend. 
  /*
     Template is of form: //(You can use a dummy dict while developing.)
     {
        "title": <title of the challenge template>,
        "image": <preview image of the challenge template>,
        "dataset": <string discribing the dataset>,
        "eval_criteria": <an array or list of strings which are the leaderboard metrics>,
        "phases": <number of challenge phases>,
        "splits": <number of dataset splits>,
     }
  */
  fetchChallengeTemplates(callback = null) {
    const SELF = this;
    var path = 'challenges/get_all_challenge_templates/';
    SELF.apiService.getUrl(path, true, true).subscribe(
      data => {
        SELF.challengeTemplates = data['results'];
      },
      err => {
        SELF.globalService.handleApiError(err);
      },
      () => {}
    );
  }

}
