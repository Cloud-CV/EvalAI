import { Component, OnInit, Input } from '@angular/core';
import { GlobalService } from '../../../services/global.service';
import { ApiService } from '../../../services/api.service';
import { AuthService } from '../../../services/auth.service';
import { ChallengeService } from '../../../services/challenge.service';
import { Router, ActivatedRoute } from '@angular/router';

/**
 * Component Class
 */
@Component({
  selector: 'app-challenge-template-card',
  templateUrl: './challenge-template-card.component.html',
  styleUrls: ['./challenge-template-card.component.scss']
})
export class ChallengeTemplateCardComponent implements OnInit {

  /**
   * Challenge object
   */
  @Input() template: object;

  /**
   * Constructor.
   * @param route  ActivatedRoute Injection.
   * @param router  Router Injection.
   * @param globalService  GlobalService Injection.
   * @param authService  AuthService Injection.
   * @param apiService  ApiService Injection.
   * @param challengeService  ChallengeService Injection.
   */
  constructor(private globalService: GlobalService,
              private apiService: ApiService,
              private authService: AuthService,
              private challengeService: ChallengeService,
              private router: Router,
              private route: ActivatedRoute) { }

  /**
   * Component on initialized.
   */
  ngOnInit() { }

  /**
   * Participate in the current challenge card (redirect).
   */
  createTemplateChallenge() {
    /*On clicking a challenge template from the view, this should be triggered, and the page should change to the template-challenge-create
    component view. 
    The component is here: app/components/template-challenge-create
    */
  }
}