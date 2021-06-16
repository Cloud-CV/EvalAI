import { Component, OnInit, Inject } from '@angular/core';
import { DOCUMENT } from '@angular/common';
import { NGXLogger } from 'ngx-logger';

// import service
import { ChallengeService } from '../../../services/challenge.service';
import { ApiService } from '../../../services/api.service';
import { EndpointsService } from '../../../services/endpoints.service';
import { GlobalService } from '../../../services/global.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-challengeevaluation',
  templateUrl: './challengeevaluation.component.html',
  styleUrls: ['./challengeevaluation.component.scss'],
})
export class ChallengeevaluationComponent implements OnInit {
  /**
   * Challenge object
   */
  challenge: any;

  /**
   * Is challenge host
   */
  isChallengeHost = false;

  /**
   * Challenge evaluation DOM element
   */
  evaluationElement: any;

  /**
   * Challenge tnc DOM element
   */
  tncElement: any;

  /**
   * To call the API inside modal for editing the challenge evaluation
   * details, evaluation script and terms and conditions
   */
  apiCall: any;

  /**
   * Constructor.
   * @param document  window document Injection.
   * @param challengeService  ChallengeService Injection.
   */
  constructor(
    private challengeService: ChallengeService,
    @Inject(DOCUMENT) private document: Document,
    private endpointsService: EndpointsService,
    private apiService: ApiService,
    private globalService: GlobalService,
    private logger: NGXLogger
  ) {}

  /**
   * Component on init function.
   */
  ngOnInit() {
    this.evaluationElement = this.document.getElementById('challenge-evaluation');
    this.tncElement = this.document.getElementById('challenge-tnc');
    this.challengeService.currentChallenge.subscribe((challenge) => {
      this.challenge = challenge;
      this.updateView();
    });
    this.challengeService.isChallengeHost.subscribe((status) => {
      this.isChallengeHost = status;
    });
  }

  /**
   * Updating view function (Called after onInit)
   */
  updateView() {
    this.evaluationElement.innerHTML = this.challenge['evaluation_details'];
    this.tncElement.innerHTML = this.challenge['terms_and_conditions'];
  }
}
