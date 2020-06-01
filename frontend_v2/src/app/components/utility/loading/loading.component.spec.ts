import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { LoadingComponent } from './loading.component';
import {AuthService} from '../../../services/auth.service';
import {GlobalService} from '../../../services/global.service';
import {ApiService} from '../../../services/api.service';
import {EndpointsService} from '../../../services/endpoints.service';
import {HttpClientModule} from '@angular/common/http';

describe('LoadingComponent', () => {
  let component: LoadingComponent;
  let fixture: ComponentFixture<LoadingComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ LoadingComponent ],
      providers: [AuthService, GlobalService, ApiService, EndpointsService],
      imports: [HttpClientModule]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(LoadingComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
