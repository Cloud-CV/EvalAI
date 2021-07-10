import { Component, OnInit, OnChanges } from '@angular/core';
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
  tabHighlight: string = "participatedChallenges";

   /**
   * Constructor
   * @param globalService  GlobalService Injection.
   */
  constructor(
    private globalService: GlobalService,
  ) {}

  ngOnInit() {
    this.globalService.nameTabHighlight.subscribe((tabHighlight) => {
      this.tabHighlight = tabHighlight;
    });
    console.log("HELLO" + this.tabHighlight);
  }
}
