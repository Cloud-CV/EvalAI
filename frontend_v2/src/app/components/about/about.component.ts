import { Component, OnInit, Inject } from '@angular/core';
import { GlobalService } from '../../services/global.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-about',
  templateUrl: './about.component.html',
  styleUrls: ['./about.component.scss'],
})
export class AboutComponent implements OnInit {
  /**
   * Constructor.
   * @param globalService  GlobalService Injection.
   */
  constructor(private globalService: GlobalService) {}

  /**
   * Component on Initialization.
   */
  ngOnInit() {
    this.globalService.scrollToTop();
  }
}
