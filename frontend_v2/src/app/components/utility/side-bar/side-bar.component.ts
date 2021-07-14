import { Component, OnInit } from '@angular/core';
import { Router, NavigationEnd } from '@angular/router';
import { filter } from "rxjs/internal/operators";
import { GlobalService } from '../../../services/global.service';

@Component({
  selector: 'app-side-bar',
  templateUrl: './side-bar.component.html',
  styleUrls: ['./side-bar.component.scss'],
})
export class SideBarComponent implements OnInit {

  /**
   * Current name of tab which needs to be active
   */
  tabHighlight: string = "allChallenges";

  /**
   * Returns true if the string is not a number
   */
  isChallengeComponent : boolean = false;

   /**
   * Constructor
   * @param globalService  GlobalService Injection.
   * @param router Router
   */
  constructor(
    private globalService: GlobalService,
    private router: Router
  ) { }

  ngOnInit() {
    this.globalService.nameTabHighlight.subscribe((tabHighlight) => {
      this.tabHighlight = tabHighlight;
    });

    this.router.events
    .pipe(filter(event => event instanceof NavigationEnd))
    .subscribe((event) => {
      if(event) {
          if(this.router.url.split('/')[2] == "me") {
            this.tabHighlight = "hostedChallenges";
            this.globalService.changeTabActiveStatus("hostedChallenges");
          }
          else if(this.router.url.split('/')[2] == "hosts") {
            this.tabHighlight = "createChallenge";
            this.globalService.changeTabActiveStatus("createChallenge");
          }
          else if(this.router.url.split('/')[2] == "participants") {
            this.tabHighlight = "myParticipantTeams";
            this.globalService.changeTabActiveStatus("myParticipantTeams");
          }
          else if(this.router.url.split('/')[2] == "participated") {
            this.tabHighlight = "participatedChallenges";
            this.globalService.changeTabActiveStatus("participatedChallenges");
          }
          else if(this.router.url.split('/')[2] == "all") {
            this.tabHighlight = "allChallenges";
            this.globalService.changeTabActiveStatus("allChallenges");
          }
        this.isChallengeComponent = isNaN(parseInt(this.router.url.split('/')[length]));
      }
  });
  }
}
