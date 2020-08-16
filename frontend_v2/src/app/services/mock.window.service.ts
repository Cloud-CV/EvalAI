import { WindowService } from './window.service';
import { Injectable } from '@angular/core';

@Injectable()
export class MockWindowService extends WindowService {
  /**
   * Mocked Load Javascript function.
   * @param url  Name of script.
   * @param implementationCode  callback function.
   * @param location  where to append the file
   * @param env  `This` variable of the environment
   */
  loadJS(url, implementationCode, location, env) {
    console.log('LoadJS mocked..');
  }
}
