import { Component, OnInit, OnChanges } from '@angular/core';
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
   * Constructor
   * @param globalService  GlobalService Injection.
   * @param router Router
   */
  constructor(
    private globalService: GlobalService,
    private router: Router
  ) {
    router.events
    .pipe(filter(event => event instanceof NavigationEnd))
    .subscribe((event) => {
      if(event) {
        if(this.tabHighlight == "hostedChallenges" || this.tabHighlight == "createChallenge" || 
        this.tabHighlight == "myParticipantTeams" ||  this.tabHighlight == "participatedChallenges" || 
        this.tabHighlight == "allChallenges") {
          if(this.router.url.split('/')[length] == "me") {
            this.tabHighlight = "hostedChallenges";
            this.globalService.changeTabActiveStatus("hostedChallenges");
          }
          else if(this.router.url.split('/')[length] == "hosts") {
            this.tabHighlight = "createChallenge";
            this.globalService.changeTabActiveStatus("createChallenge");
          }
          else if(this.router.url.split('/')[length] == "participants") {
            this.tabHighlight = "myParticipantTeams";
            this.globalService.changeTabActiveStatus("myParticipantTeams");
          }
          else if(this.router.url.split('/')[length] == "participated") {
            this.tabHighlight = "participatedChallenges";
            this.globalService.changeTabActiveStatus("participatedChallenges");
          }
          else if(this.router.url.split('/')[length] == "all") {
            this.tabHighlight = "allChallenges";
            this.globalService.changeTabActiveStatus("allChallenges");
          }
        }
        console.log("HELLO URL CHANGED" + this.tabHighlight);
      }
  });

  }

  ngOnInit() {
    this.globalService.nameTabHighlight.subscribe((tabHighlight) => {
      this.tabHighlight = tabHighlight;
    });
    console.log("HELLO WORLD" + this.tabHighlight);
  }
}
