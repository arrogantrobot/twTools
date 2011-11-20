import com.swath.*;
import com.swath.cmd.*;
import java.util.Queue;

/**
 * "Planetary Trade Route" swath script.
 * @author Rob Long
 *
 * 
 *
 * 
 */

public class PlanetaryTradeRoute extends UserDefinedScript {
    private Parameter m_planet;
    private Parameter m_min_amount;
    private Parameter m_min_percentage;
    private Parameter m_dump_creds;
    private Parameter m_num_ports;

    private int port_count;
    private int max_ports;

    private int m_amount;
    private int m_type;
    private int m_type2;
    private boolean m_buy;
    private int m_buy_amount;


    public String getName() {
        return "PlanetaryTradeRoute";
    }

    public boolean initScript() throws Exception {
        Sector sector = Swath.getSector(Swath.main.currSector());
        Planet [] planets = sector.planets();
        int planet_default = 2;
        for (Planet p : planets){
            if(p.owner().isYou()||p.owner().isYourCorporation()){
                planet_default = p.id();
                break;
            }
        }

        m_planet = new Parameter("Planet to run route with");
        m_planet.setType(Parameter.INTEGER);
        m_planet.setInteger(planet_default);

        m_num_ports = new Parameter("Number of ports to hit");
        m_num_ports.setType(Parameter.INTEGER);
        m_num_ports.setInteger(20);

        m_min_amount = new Parameter("Minimum Amount of ORG Per Port");
        m_min_amount.setType(Parameter.INTEGER);
        m_min_amount.setInteger(1000);

        m_min_percentage = new Parameter("Minimum Percentage to consider for ORG Per Port");
        m_min_percentage.setType(Parameter.INTEGER);
        m_min_percentage.setInteger(75);

        m_dump_creds=new Parameter("Dump credits into citadel after each run");
        m_dump_creds.setBoolean(false);

        registerParam(m_planet);
        registerParam(m_min_amount);
        registerParam(m_min_percentage);
        registerParam(m_dump_creds);
        registerParam(m_num_ports);

        port_count = 0;
        return true;
    }

    public boolean runScript() throws Exception {
        int holds = Swath.ship.holds();
        max_ports = m_num_ports.getInteger();

        if(atPrompt(Swath.COMPUTER_PROMPT)){
            LeaveComputer.exec();
        }
        if(atPrompt(Swath.COMMAND_PROMPT)){
            Land.exec(m_planet.getInteger());
        }
        if(atPrompt(Swath.PLANET_PROMPT)){
            EnterCitadel.exec();
        }
        while( is_ok() ){
            Sector next = find_next_sector();
            PrintText.exec("Moving to sector: "+next.sector());
            if(!atPrompt(Swath.CITADEL_PROMPT)){
                if(atPrompt(Swath.COMMAND_PROMPT)){
                    Land.exec(m_planet.getInteger());
                }
                if(atPrompt(Swath.PLANET_PROMPT)){
                    EnterCitadel.exec();
                }
            }
            if(m_dump_creds.getBoolean()){
                TakeLeaveCredits.exec( Swath.you.credits()*(-1));
            }
            PlanetWarp.exec(next);
            planetary_trade();
        }

        return true;
    }

    public Sector find_next_sector() throws Exception {
        Sector current = Swath.getSector(Swath.main.currSector());
        Tools.PortSearchParameters next = new Tools.PortSearchParameters();
        next.setMinPercentage(Swath.ORGANICS, m_min_percentage.getInteger());
        next.setMinAmount(Swath.ORGANICS, m_min_amount.getInteger());
        next.setPortOption(Swath.ORGANICS, true);
        int[] ports = Tools.findPorts( next, true, 10 );
        int count=0;
        Sector answer = Swath.getSector(ports[0]);
        while(answer.isStarDock() || !(answer.fighters()>0) || !(answer.ftrOwner().isYou() || answer.ftrOwner().isYourCorporation())  ){
            count++;
            answer = Swath.getSector(ports[count]);
        }
        return answer; 
    }   

    public boolean planetary_trade() throws Exception{

        Sector sector = Swath.getSector(Swath.main.currSector());
        LeaveCitadel.exec();
        int [] s = sector.portAmounts();
        m_amount = (s[1]-(s[1] % Swath.ship.holds()));
        m_type = Swath.ORGANICS;

        return do_trade();
    }

    public boolean do_trade() throws Exception {

        int holds = Swath.ship.holds();
        int amount = m_amount;
        int sell_amount = amount;
        int bought_amount = 0;
        int sold_amount = 0;
        int to_buy=0;
        int to_sell=0;
        int product_to_sell=0;
        int product_to_buy=0;
        int [] product = {0,0,0};
        int amount_to_pick_up=0;
        int amount_to_buy=0;
        int buy_amount = 0;

        if(m_buy){
            buy_amount = m_buy_amount;
        }

        Ship my_ship = Swath.ship;

        switch (m_type) {
            case Swath.FUEL_ORE:
                product_to_sell = 0;
                break;
            case Swath.ORGANICS:
                product_to_sell = 1;
                break;
            case Swath.EQUIPMENT:
                product_to_sell = 2;
                break;
        }
        if (m_buy) {
            switch (m_type2) {
                case Swath.FUEL_ORE:
                    product_to_buy = 0;
                    break;
                case Swath.ORGANICS:
                    product_to_buy = 1;
                    break;
                case Swath.EQUIPMENT:
                    product_to_buy = 2;
                    break;
            }
        }


        to_buy = buy_amount - bought_amount;
        to_sell = sell_amount - sold_amount;

        while ((sold_amount<sell_amount)||(bought_amount<buy_amount)) {
            if( to_sell < holds){
                amount_to_pick_up = to_sell;
            }else{
                amount_to_pick_up = holds;
            }
            if( to_buy < holds ) {
                amount_to_buy = to_buy;
            } else {
                amount_to_buy = holds;
            }
            product[0]=product[1]=product[2] = 0;
            // Land On Planet
            if(! atPrompt(Swath.PLANET_PROMPT)){
                if(atPrompt(Swath.COMPUTER_PROMPT)){
                    LeaveComputer.exec();
                }
                if(atPrompt(Swath.COMMAND_PROMPT)){
                    Land.exec(m_planet.getInteger());
                }
                if(atPrompt(Swath.CITADEL_PROMPT)){
                    LeaveCitadel.exec();
                }
            }
            if((my_ship.fuel()+my_ship.organics()+my_ship.equipment())>0){
                TakeLeaveProducts.exec(-my_ship.fuel(),-my_ship.organics(),-my_ship.equipment());
            }

            product[product_to_sell] = amount_to_pick_up;

            // Take Product
            TakeLeaveProducts.exec(product[0],product[1],product[2]);

            // Leave Planet
            LiftOff.exec();

            product[product_to_sell] *= -1;
            product[product_to_buy] = amount_to_buy;

            //Trade at Port
            Trade.exec(product[0],product[1],product[2]);

            sold_amount += amount_to_pick_up;
            bought_amount += amount_to_buy;

            to_buy = buy_amount - bought_amount;
            to_sell = sell_amount - sold_amount;

        }
        if (amount_to_buy>0) {
            // Land On Planet
            Land.exec(m_planet.getInteger());
            // Leave product
            TakeLeaveProducts.exec(-my_ship.fuel(),-my_ship.organics(),-my_ship.equipment());
        }
        if(atPrompt(Swath.COMMAND_PROMPT)){
            Land.exec(m_planet.getInteger());
        }

        return true;
    }


    public boolean is_ok(){
        if(++port_count> max_ports){
            return false;
        }
        return true;
    }


}
