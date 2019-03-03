import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { GlobalService } from '../../services/global.service';
import { EndpointsService } from '../../services/endpoints.service';
import { AuthService } from '../../services/auth.service';
import { Router, ActivatedRoute } from '@angular/router';

/**
 * Component Class
 */
@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit {

  /**
   * Challenges list
   */
  challenges = [];

  /**
   * Host teams list
   */
  hostteams = [];

  /**
   * Participant teams list
   */
  participantteams = [];

  /**
   * Constructor.
   * @param endpointsService  EndpointService Injection.
   * @param route  ActivatedRoute Injection.
   * @param router  Router Injection.
   * @param globalService  GlobalService Injection.
   * @param apiService  ApiService Injection.
   * @param authService  AuthService Injection.
   */
  constructor(private apiService: ApiService,
              private authService: AuthService,
              private globalService: GlobalService,
              private router: Router,
              private route: ActivatedRoute,
              private endpointsService: EndpointsService) { }

  /**
   * Component on initialized.
   */
  ngOnInit() {
    if (!this.authService.isLoggedIn()) {
      this.router.navigate(['auth/login']);
    }
    this.fetchChallengesFromApi(this.endpointsService.allChallengesURL('present'));
    this.fetchTeams(this.endpointsService.allParticipantTeamsURL());
    this.fetchTeams(this.endpointsService.allHostTeamsURL());
  }

  /**
   * Fetch challenges from backend.
   * @param path  Challenges fetch URL.
   */
  fetchChallengesFromApi(path) {
    const SELF = this;
    SELF.apiService.getUrl(path).subscribe(
      data => {
        SELF.challenges = data['results'];
      },
      err => {
        SELF.globalService.handleApiError(err);
      },
      () => console.log('Ongoing challenges fetched!')
    );
  }

  /**
   * Fetch teams from backend.
   * @param path  Teams fetch URL.
   */
  fetchTeams(path) {
    const SELF = this;
    let isHost = false;
    if (path.includes('hosts')) {
      isHost = true;
    }
    this.apiService.getUrl(path).subscribe(
      data => {
        if (data['results']) {
          if (isHost) {
            SELF.hostteams = data['results'];
          } else {
            SELF.participantteams = data['results'];
          }
        }
      },
      err => {
        SELF.globalService.handleApiError(err, false);
      },
      () => {
        console.log('Teams fetched for teamlist', path);
      }
    );
  }

}
